# backend

Owner: Anish. The FastAPI app, the database models, and every security check.

Status on 2026-10-09: login, patients, the screening flow, doctor review, staff accounts and the audit log are written, pass 13 tests on SQLite, and run on Render against the team's PostgreSQL database. The models in `ml/` are called from `analysis.py`; `SARCOSCAN_MODELS` chooses which load. The PDF report is made in the web app.

Read before changing anything: [API](../docs/API.md), [Database](../docs/DATABASE.md), [Security](../docs/SECURITY.md).

## Layout

```
backend/
├── main.py            app object, routers, startup (tables, schema upgrades, model loading)
├── config.py          settings from .env (ENV_FILE picks another file)
├── db.py              engine, session, get_or_404, schema upgrades
├── models.py          SQLAlchemy tables and the append-only triggers for audit_logs
├── schemas.py         Pydantic request and response models
├── crypto.py          AES-256-GCM column type for name and phone, and the phone hash
├── security.py        password hashing, the login token, role and audit dependencies
├── analysis.py        AWGS cutoffs, the sarcopenia stage rule, calls into ml/predict.py and ml/tabular.py
├── xray_checks.py     an upload's real file type, and whether it looks like an X-ray
├── storage.py         uploaded files: Cloudinary when hosted, backend/uploads/ on a laptop
├── routers/
│   ├── auth.py        signup, login, me
│   ├── patients.py    register, list and search, details
│   ├── visits.py      visit, inputs, grip, X-ray, analyze, result, review, history, files
│   └── admin.py       audit log, staff accounts
├── seed.py            creates the first admin and doctor, and the demo doctor at startup
├── tests/test_api.py
├── requirements.txt   the only Python package list
├── package.json       build and start commands for Render (its root directory is backend/)
└── uploads/           X-rays and overlays on a laptop only (created on first upload, ignored by git)
```

## Setup

From the repo root, `npm run setup` does everything once: it creates `.venv`, installs `backend/requirements.txt`, writes a local `.env` (SQLite, fresh keys, random seed passwords) if there is none, and creates the seed users. Then `npm run dev` starts this API on port 8000 together with the web app.

Run any Python command from the repo root, so that both `backend` and `ml` can be imported.

By hand, without npm:

```
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
copy .env.example .env        # then fill it in
.venv\Scripts\python -m backend.seed
.venv\Scripts\python -m uvicorn backend.main:app --reload
```

A new virtual environment ships an old pip, which fails on some networks with a certificate error. Then install with the main Python's pip instead: `python -m pip --python .venv\Scripts\python.exe install -r requirements.txt` (`npm run setup` retries this way on its own).

Two settings files, both ignored by git:

- `.env` is for local work. Everything stays on this machine: a SQLite file (`sarcoscan.db`) and `backend/uploads/`.
- `.env.prod` holds the hosted database and storage credentials. To run against it, set `ENV_FILE` first: `$env:ENV_FILE=".env.prod"` in PowerShell, then the same commands. Close that terminal afterwards so the next run is local again.

The two files have different encryption keys, so a patient saved in one database cannot be read with the other file.

Seed logins: `admin@sarcoscan.local`, `doctor@sarcoscan.local`.

## Tests

```
python -m pytest backend
```

They use a temporary SQLite file and their own keys, so they need neither PostgreSQL nor your `.env`.

## Calling the model

`backend/analysis.py` imports `analyze` from `ml/predict.py` (X-ray models) and the functions in `ml/tabular.py` (body-measurement models). Arguments and return values are in [ML](../docs/ML.md) under "Handing models to the backend". When a model is switched off with `SARCOSCAN_MODELS` or cannot load, the analyze endpoint still works: it stores the rule-based stage and leaves that model's fields empty.

## Packages to add with their features

`pydicom` if DICOM upload is supported.
