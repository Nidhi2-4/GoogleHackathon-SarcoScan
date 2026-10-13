# SarcoScan: rules for AI coding agents

Read this before changing anything in this repo. It applies to every AI assistant (Claude Code, Cursor, Antigravity, and others) and works as a checklist for people too.

## What this project is

SarcoScan is a screening tool. A knee AP X-ray plus handgrip and clinical inputs give a sarcopenia stage and an osteoporosis risk tier. It is a hackathon project (HackPulse, team CodeSharks). The full spec is `docs/Documentation - SarcoScan (2).pdf`.

Current state on 2026-10-09: the backend and the web app work together end to end, hosted on Render (API) and Vercel (web app). From the repo root: `npm run setup` once, `npm run dev` to run both, `npm run check` before a commit (the same checks as CI). Four models are connected: osteoporosis and KL grade through `ml/predict.py`, low muscle mass and bone loss through `ml/tabular.py`. Their final weight files are committed in `ml/models/` on purpose; datasets and training checkpoints are not. `docs/PLAN.md` tracks what is done.

More than one AI assistant has edited this repo at the same time. Before changing a file, read its current contents; do not overwrite work you did not write.

## Who owns what

| Area | Folder | Owner | Read first |
|---|---|---|---|
| Backend API, database, security | `backend/` | Anish | `docs/API.md`, `docs/DATABASE.md`, `docs/SECURITY.md` |
| Models, training, inference | `ml/` | Pravesh | `docs/ML.md` |
| Web UI, phone and desktop, spec document | `frontend/web/` | Nidhi | `docs/FRONTEND.md` |
| Pitch deck and demo | `docs/` | Soham | `docs/PITCH.md` |
| How the parts fit, and the task list | | everyone | `docs/ARCHITECTURE.md`, `docs/PLAN.md` |

Each area has a skill in `.claude/skills/` holding the working rules for that area. Claude Code loads them on its own. In any other tool, open the matching `SKILL.md` and follow it.

| Skill | Use it when |
|---|---|
| `sarcoscan-backend` | changing anything under `backend/` |
| `sarcoscan-frontend` | changing anything under `frontend/` |
| `sarcoscan-ml` | training, evaluating, or exporting a model, or writing `ml/predict.py` |
| `sarcoscan-pitch` | writing slides, README claims, or the demo script |
| `sarcoscan-docs-sync` | finishing any change, to bring the docs back in line |

## Rules

1. **Stay in scope.** Build what `docs/ARCHITECTURE.md` lists under "What we build first". Do not add Celery, Redis, MinIO, Orthanc, FHIR, React Native, or Electron unless a teammate asks for it.
2. **Security is enforced in the backend.** Every endpoint checks the user's role on the server, and every endpoint that touches patient data writes an audit log row. Follow `docs/SECURITY.md`. Hiding a button in the UI is not a security control.
3. **Never commit** secrets, `.env` files, datasets, zip files, real patient X-rays, or training checkpoints. `.gitignore` covers the common cases; check `git status` before committing anyway.
4. **Never invent results.** No accuracy, AUC, or sensitivity figure goes into code, docs, the README, or slides unless it was measured and recorded in the Results table in `docs/ML.md`. The numbers in the spec are targets, not results.
5. **Keep the docs true.** When a change makes a doc wrong, fix the doc in the same change. The `sarcoscan-docs-sync` skill lists which doc goes with which kind of change.
6. **Mark planned work as planned.** Docs use three statuses: `planned`, `in progress`, `done`. Do not describe unbuilt things as if they exist.
7. **Simplest thing that works.** Standard library and already-installed packages before a new dependency.
8. **Stay in the owner's folder.** If a task needs a change in another person's folder, tell the user instead of making it quietly.
