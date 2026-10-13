"""Inference code the backend calls. See "Handing models to the backend" in docs/ML.md.

Both models are DenseNet121 classifiers trained by Pravesh with the scripts in ml/training/
(reports in ml/reports/).
The weight files are not in git: copy osteoporosis_best.pt and arthritis_best.pt into ml/models/.
"""
from pathlib import Path

import torch
import torchvision
from PIL import Image
from torchvision import transforms

from . import muscle

MODELS = Path(__file__).parent / "models"
MODEL_VERSION = "osteo-densenet121-0.1+kl-densenet121-0.1"

# Same steps as eval_tf and load_xray in ml/training/train_osteoporosis.py and train_arthritis.py.
# Keep the three in step: a different resize or normalisation shifts the probabilities.
def _pad_to_square(image: Image.Image) -> Image.Image:
    """Pad with black to a square instead of squashing the knee."""
    side = max(image.size)
    square = Image.new(image.mode, (side, side), 0)
    square.paste(image, ((side - image.width) // 2, (side - image.height) // 2))
    return square


_PREPROCESS = transforms.Compose(
    [
        _pad_to_square,
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
    ]
)

# The classifier's three classes map straight onto the three tiers. No cutoff is chosen here.
_TIER = {"Normal": "low", "Osteopenia": "moderate", "Osteoporosis": "high"}


def _load(name: str) -> tuple[torch.nn.Module, list[str]]:
    # weights_only=True refuses anything in the file that is not plain tensors and names.
    checkpoint = torch.load(MODELS / name, map_location="cpu", weights_only=True)
    classes = checkpoint["classes"]
    model = torchvision.models.densenet121(weights=None)
    model.classifier = torch.nn.Sequential(
        torch.nn.Dropout(0.3), torch.nn.Linear(model.classifier.in_features, len(classes))
    )
    model.load_state_dict(checkpoint["model"])
    return model.eval(), classes


_osteo, _osteo_classes = _load("osteoporosis_best.pt")
_kl, _kl_classes = _load("arthritis_best.pt")


def _soft_tissue(image_path: str) -> dict:
    """Soft-tissue ratios and the overlay from ml/muscle.py. Empty when the image cannot be measured:
    the classifiers' answers must not be lost because a ruler could not be placed."""
    source = Path(image_path)
    overlay = source.with_name(f"{source.stem}_overlay.png")
    try:
        measured = muscle.measure(source, overlay_path=overlay)
    except Exception:  # an image-processing estimate; never let it fail the whole analysis
        return {}
    if not measured["valid"]:
        overlay.unlink(missing_ok=True)  # an overlay of a failed measurement would mislead
        return {}
    keys = ("thigh_soft_to_bone", "calf_soft_to_bone", "soft_to_plateau", "soft_area_ratio")
    return {**{key: measured[key] for key in keys}, "overlay_path": str(overlay)}


def analyze(image_path: str, age: int, sex: str, bmi: float) -> dict:
    """age, sex, and bmi are accepted but unused: both models look at the image only."""
    # ponytail: 8-bit PNG and JPG only, which is all the upload endpoint accepts. The training loader
    # also rescales 16-bit images; copy that here if DICOM or 16-bit PNG uploads are ever allowed.
    with Image.open(image_path) as image:
        batch = _PREPROCESS(image.convert("L").convert("RGB")).unsqueeze(0)
    # The image and its mirror, averaged: the same test-time step the training scripts used for
    # the reported scores. It also stops a left knee and a right knee getting different answers.
    batch = torch.cat([batch, torch.flip(batch, dims=[3])])
    with torch.inference_mode():
        osteo = torch.softmax(_osteo(batch), dim=1).mean(dim=0)
        kl = torch.softmax(_kl(batch), dim=1).mean(dim=0)
    return {
        "model_version": MODEL_VERSION,
        "osteoporosis_prob": float(osteo[_osteo_classes.index("Osteoporosis")]),
        "osteoporosis_tier": _TIER[_osteo_classes[int(osteo.argmax())]],
        "kl_grade": int(_kl_classes[int(kl.argmax())].removeprefix("KL")),
        **_soft_tissue(image_path),
        # Not built yet: Grad-CAM. low_muscle is deliberately not returned: no cutoff for the ratios exists.
    }
