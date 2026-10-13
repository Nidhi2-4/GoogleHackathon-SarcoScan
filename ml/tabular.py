"""The two models that use numbers instead of the X-ray. Not called by the backend yet.

    low_muscle(...)  sarcopenia_ANN_1.joblib        chance of low muscle mass
    bone_loss(...)   osteoporosis_XGBoost_1.joblib  chance of osteopenia or osteoporosis

Both were trained on NHANES (US survey; see ml/training/build_nhanes_dataset.py). The muscle model
saw ages 20 to 59 only. Weight files go in ml/models/ (from the team's Drive); they are not in git.

Needs: scikit-learn 1.6.1, xgboost, joblib, pandas, h5py, numpy 2.
Check it runs: python -m ml.tabular
"""
import io
import zipfile
from pathlib import Path

import h5py
import joblib
import numpy as np
import pandas as pd

MODELS = Path(__file__).parent / "models"

# joblib files run code when opened. Only load files that came from the team.
_muscle = joblib.load(MODELS / "sarcopenia_ANN_1.joblib")
_bone = joblib.load(MODELS / "osteoporosis_XGBoost_1.joblib")


def _dense_layers(keras_file: bytes) -> list[tuple[np.ndarray, np.ndarray]]:
    # ponytail: the network is three plain Dense layers, so its weights are read straight from the
    # file and multiplied here. That avoids Keras, whose 3.13 files need Python 3.11. If the network
    # ever gets another layer type, load it with Keras instead.
    with zipfile.ZipFile(io.BytesIO(keras_file)) as archive:
        weights = h5py.File(io.BytesIO(archive.read("model.weights.h5")), "r")
    names = sorted(name for name in weights["layers"] if name.startswith("dense"))
    return [(np.array(weights[f"layers/{n}/vars/0"]), np.array(weights[f"layers/{n}/vars/1"])) for n in names]


# Yes or no questions the bone-loss model knows. any_prior_fracture is worked out from the three fractures.
HISTORY = [name for name in _bone["features"] if name not in _muscle["features"]
           and name not in ("sedentary_min_per_day", "any_prior_fracture")]

_layers = _dense_layers(_muscle["keras_model_bytes"])


def _row(features: list[str], values: dict) -> pd.DataFrame:
    """One patient as the table the model expects. Anything not given is left empty; the model fills it in."""
    row = {name: values.get(name) for name in features}
    return pd.DataFrame([{name: np.nan if value is None else float(value) for name, value in row.items()}])


def low_muscle(**values) -> dict:
    """values: age, sex_male (1 or 0), race_eth, height_cm, weight_kg, bmi, waist_cm, arm_circ_cm,
    grip_max_kg, grip_combined_kg."""
    x = np.asarray(_muscle["prep"].transform(_row(_muscle["features"], values)), dtype=np.float32)
    for kernel, bias in _layers[:-1]:
        x = np.maximum(x @ kernel + bias, 0)
    kernel, bias = _layers[-1]
    probability = float(1 / (1 + np.exp(-(x @ kernel + bias)))[0][0])
    return {"probability": probability, "low_muscle": probability >= _muscle["threshold"]}


def bone_loss(**values) -> dict:
    """values: the same as low_muscle, plus any of the questionnaire answers the model knows."""
    probability = float(_bone["pipeline"].predict_proba(_row(_bone["features"], values))[0][1])
    return {"probability": probability, "bone_loss": probability >= _bone["threshold"]}


if __name__ == "__main__":
    frail = dict(age=68, sex_male=0, race_eth=6, height_cm=154, weight_kg=52, bmi=21.9, waist_cm=78,
                 arm_circ_cm=24, grip_max_kg=16.2, grip_combined_kg=31.1)
    strong = dict(age=35, sex_male=1, race_eth=6, height_cm=175, weight_kg=82, bmi=26.8, waist_cm=92,
                  arm_circ_cm=34, grip_max_kg=48, grip_combined_kg=94)
    print("frail :", low_muscle(**frail), bone_loss(**frail))
    print("strong:", low_muscle(**strong), bone_loss(**strong))
    assert low_muscle(**frail)["low_muscle"] and not low_muscle(**strong)["low_muscle"]
    assert bone_loss(**frail)["bone_loss"] and not bone_loss(**strong)["bone_loss"]
    from backend.analysis import HISTORY_QUESTIONS  # the API's copy of the question list must match

    assert set(HISTORY) == set(HISTORY_QUESTIONS), set(HISTORY) ^ set(HISTORY_QUESTIONS)
    unknown = dict(age=70, sex_male=None, height_cm=160, weight_kg=60, bmi=23.4, grip_max_kg=20)
    print("gaps  :", low_muscle(**unknown), bone_loss(**unknown))  # missing values must not crash
    print("ok")
