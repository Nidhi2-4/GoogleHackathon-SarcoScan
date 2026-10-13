---
name: sarcoscan-backend
description: Working rules for the SarcoScan backend (FastAPI endpoints, SQLAlchemy models, login and tokens, role checks, audit log, X-ray upload, calling the ML code). Use whenever you create or change anything under backend/.
---

# SarcoScan backend

The facts live in the docs. Read the ones your change touches before writing code:

- Endpoints and who may call them: `docs/API.md`
- Tables and columns: `docs/DATABASE.md`
- Security rules and their status: `docs/SECURITY.md`
- How the backend calls the model: `docs/ML.md`, section "Handing models to the backend"
- File layout and setup commands: `backend/README.md`

Owner of this folder: Anish. If a task needs a change outside `backend/`, tell the user instead of making it quietly.

## Adding or changing an endpoint

1. Find the endpoint in `docs/API.md`. If it is not listed, add a row first: method, path, purpose, roles, status.
2. Put the route in the matching file under `backend/routers/`. All paths start with `/api/v1`.
3. Require a logged-in user and an allowed role through the shared dependency in `backend/security.py`. Do not write role checks inside the route body.
4. If the route reads or writes patient data, record it through the shared audit dependency, with action VIEW, CREATE, UPDATE, or DOWNLOAD.
5. Validate input with a Pydantic model. Never trust an id, a role, or a file name sent by the client.
6. Query with SQLAlchemy. Never build SQL by joining strings.
7. Return the status codes listed under "Conventions" in `docs/API.md`.
8. Set the endpoint's status in `docs/API.md`. If you added or changed a column, update `docs/DATABASE.md`. If you finished a security item, update the checklist in `docs/SECURITY.md`.

## Rules that are easy to break

- **Passwords:** argon2 hash only. Never store, log, or return a plain password.
- **Login token:** one JWT, 7 days, returned in the response body by `/auth/login` and `/auth/signup`. The user and role are read from the database through the verified token, never from the request. No refresh cookie and no rate limit while this is a test build; `docs/SECURITY.md`, "Before real patient data", lists what to put back.
- **Uploads:** reject over 50 MB, detect the type from the file's first bytes, save under a server-generated UUID name inside `backend/uploads/`, and serve files only through the authenticated endpoints.
- **Encrypted columns:** patient name and phone go through the shared encrypted column type (AES-256-GCM, key from `.env`). Search phone through `phone_hash`. Never put a decrypted value in a log, an audit row, or an error message.
- **Audit rows are append-only.** Never update or delete them; database triggers reject it.
- **Role checks are dependencies, not middleware.**
- **CORS:** leave it closed. The UI reaches the API through the same origin.
- **Logs:** no passwords, tokens, or patient names.
- **Secrets:** read from `.env`. Never hard-code one, even in a seed script.

## Calling the model

- Import the functions from `ml/predict.py` and call them inside the analyze endpoint. No queue, no background worker.
- Wrap the call in try/except. If the model raises, return an error the user can act on ("could not analyse this image, try another") and log the exception without patient details.
- Time the call and store it in `analysis_results.inference_ms`.
- If `ml/predict.py` does not exist yet, use a placeholder function with the same name and say so in `docs/PLAN.md`. Do not invent model outputs anywhere else.

## Out of scope unless a teammate asks

Celery, Redis, MinIO, Orthanc, FHIR, Alembic, multi-hospital support, patient login.

## Before you say it is done

- Start the app and call the endpoint once with each role. A role the table in `docs/SECURITY.md` marks "No" must get 403.
- Leave one pytest that fails if that role check is removed.
- Run `git status` and confirm no `.env`, upload, or model checkpoint is staged.
