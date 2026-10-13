# ml

Owner: Pravesh. Datasets, training, and the inference code the backend calls.

Everything about the models, the datasets, and how to report results is in [docs/ML.md](../docs/ML.md). Read it first.

## Layout

```
ml/
├── data/                  Kaggle datasets. Folders are in git, contents are ignored.
│   ├── osteoporosis/
│   │   ├── main/          train and validate
│   │   └── external/      test only
│   └── kl_grade/
│       ├── main/          train and validate
│       ├── external/      test only
│       └── cgmh/          test only (hospital data, doctor-graded)
│   └── samples/           test X-rays; `web/` holds 22 openly licensed ones with CREDITS.md
├── training/              Pravesh's scripts: dataset cleaning, duplicate checks, splits, training
├── models/                the four weight files the backend loads. Not in git: copy them in from the team's Drive.
├── reports/               training reports and plots (in git)
├── predict.py             functions the backend imports (the two X-ray models, and muscle.py)
├── muscle.py              soft-tissue to bone ratios and the overlay, by image processing
└── tabular.py             the two models that use body measurements and history; the backend calls it
```

## Rules

- Training checkpoints stay out of git. Only the final model goes in `models/`.
- A model is not mentioned anywhere until its numbers are in the Results table in `docs/ML.md`.
- Check for overlap between `main` and `external` before reporting a test score.
