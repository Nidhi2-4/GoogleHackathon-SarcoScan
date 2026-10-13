"""Cutoffs, the sarcopenia stage rule, and the calls into the models in ml/. See docs/ML.md."""
import logging
import os
from pathlib import Path

from .models import Stage

log = logging.getLogger(__name__)

# Which model groups to load: "xray" (ml/predict.py) and "tabular" (ml/tabular.py). Together they
# need more than 512 MB, so a small server can switch one or both off: SARCOSCAN_MODELS=xray,
# =tabular, or =none. The app then says what is not connected and still runs.
_ENABLED = {name.strip() for name in os.environ.get("SARCOSCAN_MODELS", "xray,tabular").split(",")}


# ── AWGS 2019 cutoffs and the stage rule ──

GRIP_CUTOFF_KG = {"male": 28.0, "female": 18.0}
CHAIR_STAND_SLOW_SEC = 12.0
SARCF_POSITIVE = 4


def grip_cutoff(sex: str) -> float:
    # ponytail: AWGS gives a cutoff for men and for women only. "other" uses the lower one
    # until a clinician decides what it should be.
    return GRIP_CUTOFF_KG.get(sex, GRIP_CUTOFF_KG["female"])


def sarcopenia_stage(
    sex: str, grip_kg: float | None, chair_stand_sec: float | None, low_muscle: bool | None
) -> Stage:
    """The rule in docs/ML.md. low_muscle is None when neither the X-ray nor the tabular model gave one."""
    low_grip = grip_kg is not None and grip_kg < grip_cutoff(sex)
    slow = chair_stand_sec is not None and chair_stand_sec >= CHAIR_STAND_SLOW_SEC
    if not (low_grip or slow):
        return Stage.none
    if not low_muscle:
        return Stage.possible
    return Stage.severe if (low_grip and slow) else Stage.probable


# ── X-ray models: ml/predict.py ──


def _xray_analyze():
    """ml.predict.analyze, or None when it is switched off or cannot load (torch or a weight file missing)."""
    if "xray" not in _ENABLED:
        return None
    try:
        from ml.predict import analyze
    except (ImportError, FileNotFoundError) as error:
        log.warning("X-ray models not connected: %s", error)
        return None
    return analyze


def model_connected() -> bool:
    return _xray_analyze() is not None


def run_model(image_path: Path, age: int, sex: str, bmi: float) -> dict:
    """Call ml/predict.py. Returns {} when the X-ray models are not connected."""
    analyze = _xray_analyze()
    if analyze is None:
        return {}
    return analyze(image_path=str(image_path), age=age, sex=sex, bmi=bmi)


# ── Body-measurement models: ml/tabular.py ──

# The yes or no questions of the bone-loss model (ml/tabular.py HISTORY). Kept here as well so the
# API can check the keys without loading the model; `python -m ml.tabular` compares the two lists.
HISTORY_QUESTIONS = (
    "diabetes", "prediabetes", "hypertension", "high_cholesterol", "arthritis", "heart_failure",
    "coronary_heart_disease", "heart_attack", "stroke", "liver_condition", "cancer", "gout", "weak_kidneys",
    "smoker_ever", "smoker_current", "vigorous_recreation", "moderate_recreation",
    "prior_hip_fracture", "prior_wrist_fracture", "prior_spine_fracture", "steroid_use", "parent_hip_fracture",
)


def _tabular():
    """The ml.tabular module, or None when it is switched off or cannot load."""
    if "tabular" not in _ENABLED:
        return None
    try:
        from ml import tabular
    except (ImportError, FileNotFoundError) as error:
        log.warning("Tabular models not connected: %s", error)
        return None
    return tabular


def tabular_connected() -> bool:
    return _tabular() is not None


def run_tabular_models(
    age: int, sex: str, height_cm: float, weight_kg: float, bmi: float,
    waist_cm: float | None, arm_circ_cm: float | None, best_left: float | None, best_right: float | None,
    history: dict[str, bool] | None,
) -> dict:
    """The two models in ml/tabular.py: low_muscle, low_muscle_prob, bone_loss, bone_loss_prob.
    Returns {} when they are not connected or no grip reading exists.
    Anything not measured is passed as None and the model fills it in."""
    grips = [g for g in (best_left, best_right) if g is not None]
    tabular = _tabular() if grips else None
    if tabular is None:
        return {}
    body = dict(
        age=age,
        sex_male={"male": 1, "female": 0}.get(sex),
        height_cm=height_cm,
        weight_kg=weight_kg,
        bmi=bmi,
        waist_cm=waist_cm,
        arm_circ_cm=arm_circ_cm,
        grip_max_kg=max(grips),
        # NHANES combined grip is the best of each hand added together.
        grip_combined_kg=sum(grips) if len(grips) == 2 else None,
        # race_eth is a US survey code with no meaning here, so it is never sent.
    )
    muscle = tabular.low_muscle(**body)
    answers = {}
    if history is not None:
        answers = {name: int(bool(history.get(name))) for name in HISTORY_QUESTIONS}
        answers["any_prior_fracture"] = int(any(answers[f"prior_{b}_fracture"] for b in ("hip", "wrist", "spine")))
    bone = tabular.bone_loss(**body, **answers)
    return {
        "low_muscle": muscle["low_muscle"],
        "low_muscle_prob": muscle["probability"],
        "bone_loss": bone["bone_loss"],
        "bone_loss_prob": bone["probability"],
    }
