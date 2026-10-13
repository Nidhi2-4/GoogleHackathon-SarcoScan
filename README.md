# SarcoScan

**Team CodeSharks · HackPulse**

A screening tool that combines a routine knee AP X-ray with a handgrip test to flag sarcopenia and osteoporosis risk, with no DEXA or CT needed.

> Status on 2026-10-09: the web app and the backend work end to end: sign in, register a patient, enter handgrip and clinical inputs, upload an X-ray, run the screening, doctor review, PDF report. Four models are connected: osteoporosis and KL grade from the X-ray, low muscle mass and bone loss from body measurements. The sarcopenia stage applies the AWGS 2019 rules to grip, chair-stand time and the models' low-muscle answer. The hosted API loads the two measurement models only (free-plan memory, see [docs/DEPLOY.md](docs/DEPLOY.md)). Numbers in this README are targets to validate, not measured results.

## Problem statement

Sarcopenia (age-related loss of muscle mass and strength) is under-diagnosed in elderly patients. Confirming it needs DEXA or CT, which Tier-2 and Tier-3 hospitals often do not have. As a result, patients are diagnosed late, usually after a fall or a fragility fracture.

Two things are already done routinely in these hospitals: knee X-rays and handgrip tests. Nobody combines them to assess muscle health.

## What it does

1. A doctor registers the patient and enters handgrip strength (3 trials per hand) and optional clinical inputs (SARC-F, 5-chair-stand time, calf circumference).
2. The doctor uploads the knee AP X-ray. The server checks the file and stores it.
3. "Run screening" works out the sarcopenia stage (None / Possible / Probable / Severe). When a model is connected it also gives an osteoporosis risk tier, the soft-tissue-to-bone ratios, and an overlay.
4. The doctor reviews the result, can override the stage, and downloads a one-page PDF report.
5. Each patient's visits build a trend over time.

The claim the project still has to prove is that **X-ray plus grip screens better than grip strength alone**.

### What it is not

- Not a replacement for DEXA. It is a screening and referral tool, not a confirmed diagnosis.
- Not an osteoarthritis diagnosis (the KL grade is an informational bonus).
- Not a treatment prescription.

## Who uses it

| User | What they do |
| --- | --- |
| Orthopedic or geriatric doctor | Registers their patients, enters grip, uploads the X-ray, runs the screening, reviews the result, decides on referral. Sees only their own patients. |
| Hospital admin | Creates and switches off staff accounts, reads the audit log, can read every patient but change none |

## How it is built

```
Browser (desktop or phone)
        |
  Next.js web app  (frontend/web)      forwards /api to the backend, so there is one origin
        |
  FastAPI backend  (backend)           login, roles, encryption, audit log, screening rules
    |          |             |
 Database    X-ray files  ml/  predict.py (X-ray models), tabular.py, muscle.py
 SQLite locally, PostgreSQL (Supabase) when hosted
```

Where it runs:

| Part | Local (`npm run dev`) | Hosted |
|---|---|---|
| Web app | http://localhost:3000 | Vercel (`frontend/web`) |
| API | http://127.0.0.1:8000 | Render (root directory `backend`, `render.yaml`) |
| Database | `sarcoscan.db` (SQLite file) | Supabase PostgreSQL |
| Files | `backend/uploads/` | Cloudinary only, private (nothing on the server's disk) |

Steps and limits for hosting are in [docs/DEPLOY.md](docs/DEPLOY.md).

The spec also describes a task queue, object storage, PACS integration, FHIR export, and a native mobile app. Those are not built; [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) lists what was left out and when it comes back.

## Repository structure

| Path | What is in it | Owner |
|---|---|---|
| `backend/` | FastAPI app, database models, security, tests ([backend/README.md](backend/README.md)) | Anish |
| `frontend/web/` | Next.js web app: the clinic dashboard and the public site | Nidhi |
| `frontend/mobile/` | Expo template for the mobile app, not started. Phones use the web app for now. | Nidhi |
| `ml/` | Model weights, inference code (`predict.py`, `tabular.py`, `muscle.py`), training scripts, reports | Pravesh |
| `docs/` | Spec, pitch deck, and the design docs listed below | Soham (pitch); each doc names its owner |
| `scripts/` | `run.mjs` and `setup.mjs`, behind the npm commands below | Anish |
| `.github/` | CI: backend tests, web lint and build on every push | Anish |
| `package.json` | The commands for the whole project (no packages of its own) | Anish |
| `render.yaml` | Render blueprint for the API | Anish |
| `deploy/huggingface/` | Dockerfile for running the API on a Hugging Face Space (all four models) | Anish |
| `.env.example` | Every setting the API reads, with how to make each value | Anish |
| `AGENTS.md` | Rules for AI coding assistants (`CLAUDE.md` points to it) | everyone |

## Getting started

Needs Node 20+ and Python 3.10 or 3.11. From the repo root:

```
npm run setup     # once: .venv + Python packages, web packages, a local .env, seed users
npm run dev       # API (auto-reload) + web app together; Ctrl+C stops both
```

Open http://localhost:3000. `npm run setup` prints the two seed logins (`admin@` and `doctor@sarcoscan.local`); they are also in `.env`.

| Command | Does |
|---|---|
| `npm run dev` | API on 8000 with auto-reload, web app on 3000 |
| `npm start` | Same, with the production web build (builds once if needed). On Render, or with `ONLY=api`, the API only |
| `npm test` | Backend tests |
| `npm run lint` / `npm run build` | Web app checks |
| `npm run check` | All of the above, the same as CI |
| `npm run seed` | Create the seed users again (the public demo doctor `demo1@doctor.com` is made by the API at startup) |

Other ports: `API_PORT=8010 PORT=3010 npm run dev`. To run against the hosted database, set `ENV_FILE=.env.prod` first (see [backend/README.md](backend/README.md)).

## Documentation

| File | Answers |
| --- | --- |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | How the parts fit, and what is cut from the spec and why |
| [docs/PLAN.md](docs/PLAN.md) | Who does what, and what is done |
| [docs/API.md](docs/API.md) | Which endpoints exist and who may call them |
| [docs/DATABASE.md](docs/DATABASE.md) | Tables and columns |
| [docs/SECURITY.md](docs/SECURITY.md) | Login, tokens, roles, encryption, uploads, audit log, and the checklist |
| [docs/ML.md](docs/ML.md) | Datasets, models, checks, results, and how a model plugs into the backend |
| [docs/FRONTEND.md](docs/FRONTEND.md) | The web app: structure, data flow, screens, and the plan for phone and desktop |
| [docs/PITCH.md](docs/PITCH.md) | What the deck may claim, and the demo script |

## Targets to validate

| Metric | Target (pilot) |
| --- | --- |
| Fusion model AUC vs grip alone | Higher, statistically significant (DeLong test) |
| Sensitivity at screening threshold | 85% or higher |
| Osteoporosis AUC vs DXA labels | 0.80 or higher |
| Inference time | Under 5 s on an i5 CPU, 16 GB RAM, no GPU |
| Time per patient | Under 5 minutes |

None of these has been measured yet.

## Data and privacy

Patient X-rays, DICOM files, generated reports, `.env` files, keys, datasets and training checkpoints must never be committed. `.gitignore` covers the common cases; check `git status` before every commit.

## Disclaimer

SarcoScan is a hackathon prototype for research and demonstration. It is not a medical device and must not be used for clinical decisions.
