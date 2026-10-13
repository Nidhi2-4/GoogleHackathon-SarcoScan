"""Cutoffs, the sarcopenia stage rule, and the call into the ML code. See docs/ML.md."""
import logging
from pathlib import Path

from .models import Stage

log = logging.getLogger(__name__)

# AWGS 2019.
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
    """The rule in docs/ML.md. low_muscle is None when no image measurement exists."""
    low_grip = grip_kg is not None and grip_kg < grip_cutoff(sex)
    slow = chair_stand_sec is not None and chair_stand_sec >= CHAIR_STAND_SLOW_SEC
    if not (low_grip or slow):
        return Stage.none
    if not low_muscle:
        return Stage.possible
    return Stage.severe if (low_grip and slow) else Stage.probable


def _model():
    """ml.predict.analyze, or None when it cannot load on this machine:
    torch is not installed, or the weight files are not in ml/models/ (they are not in git)."""
    try:
        from ml.predict import analyze
    except (ImportError, FileNotFoundError) as error:
        log.warning("AI model not connected: %s", error)
        return None
    return analyze


# The yes or no questions of the bone-loss model (ml/tabular.py HISTORY). Kept here as well so the
# API can check the keys without loading the model; a test compares the two lists.
HISTORY_QUESTIONS = (
    "diabetes", "prediabetes", "hypertension", "high_cholesterol", "arthritis", "heart_failure",
    "coronary_heart_disease", "heart_attack", "stroke", "liver_condition", "cancer", "gout", "weak_kidneys",
    "smoker_ever", "smoker_current", "vigorous_recreation", "moderate_recreation",
    "prior_hip_fracture", "prior_wrist_fracture", "prior_spine_fracture", "steroid_use", "parent_hip_fracture",
)


def run_tabular_models(
    age: int, sex: str, height_cm: float, weight_kg: float, bmi: float,
    waist_cm: float | None, arm_circ_cm: float | None, best_left: float | None, best_right: float | None,
    history: dict[str, bool] | None,
) -> dict:
    """The two models in ml/tabular.py: low_muscle, low_muscle_prob, bone_loss, bone_loss_prob.
    Returns {} when they cannot load on this machine or no grip reading exists.
    Anything not measured is passed as None and the model fills it in."""
    grips = [g for g in (best_left, best_right) if g is not None]
    if not grips:
        return {}
    try:
        from ml import tabular
    except (ImportError, FileNotFoundError) as error:
        log.warning("Tabular models not connected: %s", error)
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


def model_connected() -> bool:
    return _model() is not None


def tabular_connected() -> bool:
    """True when the two body-measurement models load on this machine."""
    try:
        from ml import tabular  # noqa: F401
    except (ImportError, FileNotFoundError) as error:
        log.warning("Tabular models not connected: %s", error)
        return False
    return True


def run_model(image_path: Path, age: int, sex: str, bmi: float) -> dict:
    """Call ml/predict.py. Returns {} when the model is not connected."""
    analyze = _model()
    if analyze is None:
        return {}
    return analyze(image_path=str(image_path), age=age, sex=sex, bmi=bmi)
