# Deploying

Owner: Anish. Last updated: 2026-10-12.

Status: the API is live on Render at https://hackpulse-codesharks.onrender.com and the web app on Vercel. On 2026-10-04 one full screening was run against the API with all four models: same result as on the laptop, 45 seconds there (about 0.3 on the laptop). The free plan's memory does not hold all four, so the API now runs with `SARCOSCAN_MODELS=tabular`; on 2026-10-09 `/api/v1/health` answered `"model_connected": false, "tabular_connected": true`.

## Before deploying

`npm run check` runs what CI runs (backend tests, web lint, web build). CI (`.github/workflows/ci.yml`) runs it on every push; deploy only a commit where it passed.

Locally the whole stack starts with `npm run dev` (see the root README). Hosted, the two halves are separate services:

## What runs where

| Part | Where | Notes |
|---|---|---|
| API | Render web service `sarcoscan-api`, root directory `backend` | `npm start` starts uvicorn on `$PORT` |
| Web app | Vercel project, root directory `frontend/web` | Next.js; forwards `/api` to the API, so the browser sees one origin |
| Database | Supabase | the `DATABASE_URL` in `.env.prod` |
| X-ray files | Cloudinary only, as private "authenticated" images | nothing is kept on the API's disk; the API refuses to start if `CLOUDINARY_URL` is missing |

## Steps

1. Push `main` to GitHub.
2. API: in Render, New, Blueprint, choose the repo. Render reads `render.yaml` and shows `sarcoscan-api`. Type in `DATABASE_URL`, `JWT_SECRET`, `FIELD_KEY`, `HASH_KEY` and `CLOUDINARY_URL` from `.env.prod`. Use the same `FIELD_KEY` and `HASH_KEY` as the database was filled with, or stored patient names cannot be read.
3. Deploy the API. Open `https://<api>.onrender.com/api/v1/health`; it should answer `{"status":"ok", ...}` and say which models are connected.
4. Web app: in Vercel, Add New, Project, choose the repo and set Root Directory to `frontend/web` (Vercel detects Next.js). Add the environment variable `BACKEND_URL` with the API's address (no slash at the end), then deploy. It is read at build time: change it, redeploy.
5. Open the web app and sign in with a seed account. If the database is new, run `npm run seed` once from your own machine with `ENV_FILE=.env.prod` set.

## Settings by hand (when a service was not made from the blueprint)

Render, the API:

| Setting | Value |
|---|---|
| Root Directory | `backend` |
| Build Command | `npm run build` (runs `pip install -r requirements.txt`, from `backend/package.json`) |
| Start Command | `npm start` (on Render it starts only the API, on `$PORT`) |
| Health Check Path | `/api/v1/health` |
| Environment | `PYTHON_VERSION=3.11.9`, `SARCOSCAN_MODELS=tabular`, `STORAGE_BACKEND=cloudinary`, and the five values from step 2 |

Render runs these commands inside `backend/`. `npm start` there calls `scripts/run.mjs`, which starts uvicorn from the repo root, so `backend` and `ml` can both be imported (running `uvicorn backend.main:app` directly inside `backend/` fails with `No module named 'backend'`). With a root directory set, Render redeploys only when files under `backend/` change: after a change in `ml/` only, use Manual Deploy.

Vercel, the web app:

| Setting | Value |
|---|---|
| Root Directory | `frontend/web` |
| Framework Preset | Next.js (detected); build and start commands left at Vercel's defaults |
| Environment | `BACKEND_URL`, the API's address with no slash at the end |

## All four models, free: Hugging Face Spaces

Status: planned (files written on 2026-10-12, not yet run). Render's free plan has memory for the measurement models only. A free Hugging Face Space has 16 GB, so it runs all four. The web app stays on Vercel and the database on Supabase.

1. huggingface.co, New Space: any name, SDK **Docker**, blank template, hardware "CPU basic" (free), **Public**.
2. In the Space, Files, upload `deploy/huggingface/Dockerfile` and `deploy/huggingface/README.md` from this repo (replace the README it made).
3. Space Settings, "Variables and secrets", add as **secrets**: `DATABASE_URL`, `JWT_SECRET`, `FIELD_KEY`, `HASH_KEY`, `CLOUDINARY_URL`, with the same values as on Render.
4. Wait for the build (about 5 minutes). `https://<user>-<space>.hf.space/api/v1/health` should say `"model_connected":true`.
5. Vercel, project Settings, Environment Variables: set `BACKEND_URL` to `https://<user>-<space>.hf.space`, then redeploy.

New code: push to GitHub, then Space Settings, "Factory rebuild". A free Space sleeps after 48 hours without a visit; the next request wakes it.

## Limits to know before the demo

- **Memory.** The free plan gives 512 MB. The four model files are in the repo; the groups named in `SARCOSCAN_MODELS` load at start. All four need more than 512 MB, and the service is then killed while starting (the log ends with "No open ports detected" or "Out of memory"). `render.yaml` sets `tabular` (muscle mass and bone loss from measurements), which fits. The other values are `xray,tabular` (everything), `xray` (osteoporosis, KL grade, overlay) and `none` (rules only). The app says which part is not connected. A 2 GB instance runs everything.

  Measured on Anish's Windows laptop on 2026-10-04 (process memory after one screening; Linux will differ somewhat):

  | `SARCOSCAN_MODELS` | Peak memory |
  |---|---|
  | `xray,tabular` | 669 MB |
  | `xray` | 490 MB |
  | `tabular` | 278 MB |
  | `none` | 125 MB |

  So all four do not fit in 512 MB, `xray` is at the edge, and `tabular` fits with room to spare.
- **Sleep.** A free service sleeps after 15 minutes without a request. The next request waits about a minute. An uptime monitor (UptimeRobot, every 5 minutes) pointed at `/api/v1/ping` keeps it awake.
- **Files.** X-rays and overlays live only on Cloudinary, so restarts and redeploys lose nothing. The API fetches them with a signed link and passes them to the browser; the model gets a temporary copy that is deleted after the analysis. Images uploaded before 2026-10-10 were on the disk and are gone; their results still show, the image shows "could not be loaded".
- **Upload size.** Requests pass through Vercel to the API. Keep X-rays to a few MB.

## Before going live

- Change the two seed passwords in the production database.
- The login page shows one public demo doctor (`demo1@doctor.com`, password on the page). The API creates it at every startup if it is missing, so nothing has to be run. Before real use: remove `seed.demo_doctor()` from `backend/main.py`, deactivate the account, and remove the "Try the demo" box from `frontend/web/src/app/login/page.tsx`.
- Login is in test mode: anyone can create a doctor account, and the token sits in the browser. Do the list under "Before real patient data" in `SECURITY.md` first.
- The `/demo` page shows made-up numbers. Label it or remove it.
