---
name: sarcoscan-ml
description: Working rules for SarcoScan model work (dataset layout, training image classifiers, overlap and leakage checks, reporting metrics honestly, exporting models, writing ml/predict.py for the backend). Use whenever you train, evaluate, or export a model, or change anything under ml/.
---

# SarcoScan ML

Read `docs/ML.md` first. It lists what the product needs from ML, the datasets, the checks, and the hand-off to the backend. This skill is the short list of rules to follow while working.

Owner of this folder: Pravesh. If a task needs a change outside `ml/`, tell the user instead of making it quietly.

## Where things go

| Thing | Place |
|---|---|
| Kaggle datasets | `ml/data/<task>/<main, external, or cgmh>/` (git ignores the contents) |
| Training scripts | `ml/training/` |
| Final model files | `ml/models/` (not in git; shared through the team's Drive) |
| Training reports and plots | `ml/reports/` |
| Inference for body-measurement models | `ml/tabular.py` |
| Inference code for the backend | `ml/predict.py` |
| Measured results | Results table in `docs/ML.md` |

Training checkpoints, zip files, and dataset images never go into git.

## Rules

1. **Images go to a CNN.** Fine-tune a pretrained ResNet18 or EfficientNet-B0. Do not flatten pixels into XGBoost. XGBoost is for tabular inputs only.
2. **Check for overlap before reporting a test score.** Hash the files in `main` and `external` (snippet in `docs/ML.md`) and remove any image that appears in both.
3. **Keep augmented copies together.** All variants of one original image stay on the same side of the split.
4. **Report the full picture.** Accuracy, macro-F1, recall per class, one-vs-rest AUC, and the confusion matrix, on the internal test split and on the external dataset separately.
5. **Record every result.** Add a row to the Results table in `docs/ML.md` with the date, the training data, both test scores, and notes (including how many overlapping images were removed).
6. **Never state a number that is not in that table.** The figures in the spec are targets. Do not copy them into code comments, docs, or slides as if they were achieved.
7. **Call a heuristic a heuristic.** The threshold-based mask, the muscle ratios, and the rule-based sarcopenia stage are prototypes. The cutoff for "low muscle proxy" is not validated. Do not output a sarcopenia probability from rules.
8. **No real patient data.** Public dataset images only.

## Writing ml/predict.py

- Load each model once, at import time.
- Functions take a file path and the patient's inputs, and return plain Python values.
- Write the overlay image next to the uploaded file and return its path.
- Raise a clear exception when an image cannot be analysed.
- Every package it imports must be added to `backend/requirements.txt`.
- Measure the time for one analysis on a CPU and write it in `docs/ML.md`. The spec's target is under 5 seconds.

## Before you say it is done

- The Results table in `docs/ML.md` has a row for the model.
- The status column in "What the product needs from ML" is updated.
- The matching box in `docs/PLAN.md` is ticked.
- `git status` shows no dataset files, zips, or checkpoints staged.
