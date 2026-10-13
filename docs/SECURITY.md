# Security

Owner: Anish. Last updated: 2026-10-12.

Status: the backend controls are built and tested, and the web app uses them. **Test build since 2026-10-12:** login was made simple on purpose while the database holds made-up patients only (open sign-up, one 7-day token in the browser, no rate limit, no password length rule, a public demo doctor). "Before real patient data" below lists what to put back. The audit triggers were checked on PostgreSQL. Nothing has run over HTTPS yet. The checklist at the bottom tracks each item; update it as items change.

## The main idea

Security comes from the backend, not from the platform. Web, mobile, and desktop all talk to the same API. If the API checks every request properly, all three are protected. If it does not, no client can make up for it. A desktop app is not safer than a web app by itself.

So the backend must do four things on every request: know who is calling, check that their role allows the action, validate what they sent, and record what they did.

## 1. Passwords and login

- Hash passwords with argon2 (for example the `argon2-cffi` or `pwdlib` package). Never store, log, or return a plain password.
- Give the same error for "no such email" and "wrong password", so the login form does not reveal which emails exist.
- A seed script creates the first admin and doctor. Their passwords come from `.env`, not from the code.
- Anyone can create a doctor account at `/auth/signup` (test build). A new doctor has no patients and cannot see anyone else's. Admin accounts are made only by an admin.
- The API creates the public demo doctor (`demo1@doctor.com`, password shown on the sign-in page) at startup: `demo_doctor` in `backend/seed.py`, called from `backend/main.py`.

## 2. The login token

One token, as simple as it gets (the spec, page 21, asks for two; that design was removed on 2026-10-12 for the test build):

- `/auth/login` and `/auth/signup` return a JWT holding the user id, signed with a long random secret from `.env`. It lasts 7 days.
- The web app keeps it in `localStorage` and sends it in the `Authorization` header. A foreign site cannot set that header, so there is no cross-site request problem.
- Every request looks the user up again, so switching an account off takes effect at once.
- Logging out deletes the token from the browser. The server keeps no session list.

### Before real patient data

- A script injected into the page could read a token in `localStorage`. Move it back to a short token in memory plus an `HttpOnly`, `Secure`, `SameSite=Strict` refresh cookie (the earlier design is in git history before 2026-10-12).
- Close `/auth/signup`, or ask for an invite code.
- Put back the login rate limit and a password minimum of 8 characters.
- Remove the demo doctor: the call in `backend/main.py`, the account, and the "Try the demo" box on the sign-in page.

## 3. One origin for UI and API

Serve the UI and the API from the same origin: the web app forwards `/api` to the backend (see `FRONTEND.md`). Then:

- CORS stays closed. Do not add `allow_origins=["*"]`.
- The mobile and desktop shells open the same URL, so they use exactly the same login flow.

## 4. Roles

The server checks the role on every endpoint with one shared dependency. Two roles since 2026-10-10 (the spec, page 21, also has a technician; the team dropped it because the doctor does the whole screening):

| Action | Doctor | Admin | Patient |
|---|---|---|---|
| Register patient | Yes, becomes that patient's doctor | No | No |
| Run screening | Own patients only | No | No |
| View results | Own patients only | All patients, read only | Own only (later) |
| Override or review | Own patients only | No | No |
| Generate report | Own patients only | No | No |
| Manage users and devices | No | Yes | No |
| View audit logs | No | Yes | No |

**Each patient belongs to one doctor** (`patients.doctor_id`, set to the doctor who registers them). `own_patient` and `own_visit` in `backend/security.py` enforce it on every patient, visit, result and X-ray endpoint. Another doctor gets the same 404 as for a patient that does not exist, so they cannot even learn the patient is there. Lists return only the doctor's own patients and visits.

Old technician accounts stay in the database, because audit rows point to them, but are switched off at every startup and can no longer be created.

The role comes from the user's row, found through the verified token, never from the request body or a query parameter. The UI may hide buttons a role cannot use, but that is for convenience only.

Use a FastAPI dependency for this, not a middleware. A middleware runs before routing and does not know which roles the matched endpoint allows; a dependency is declared on the endpoint itself.

Patient login is not part of the hackathon build, so only the three staff roles exist.

## 5. X-ray uploads

Uploaded files are the riskiest input in the system.

- Reject files over 50 MB (spec FR-1) before reading them into memory.
- Decide the file type from its content, not its name or extension:
  - PNG starts with bytes `89 50 4E 47`
  - JPEG starts with `FF D8 FF`
  - DICOM has the letters `DICM` at byte offset 128
- Then open the file with the image library inside a try/except. If it does not decode, reject it.
- Save it under a name the server generates (a UUID). Never use the client's file name in a path.
- Keep `backend/uploads/` out of any publicly served folder. X-rays and overlays are returned only by the two authenticated endpoints in `API.md`.

### X-rays on Cloudinary

An X-ray is patient data wherever it sits. The hosted API keeps X-rays and overlays only on Cloudinary (`STORAGE_BACKEND=cloudinary`, `backend/storage.py`):

- Upload them as private or authenticated assets. A default upload can be opened by anyone who has the link, with no login.
- Give clients only signed links that expire, or keep serving the file through the authenticated endpoints. SarcoScan does the second: the API fetches the file with a signed link and the browser never sees a Cloudinary URL.
- Use it only with public dataset images. Real patient X-rays stay on the hospital's server; that is the product's promise.

DICOM files carry the patient's name, ID, and birth date in their headers. If DICOM upload is supported, convert on arrival: read the pixel data with `pydicom`, save it as a PNG, and discard the uploaded file. The headers are then never stored, logged, or returned. This does not remove text that is burned into the picture itself.

## 6. Audit log

Every read or write of patient data adds a row to `audit_logs`: who, which action (VIEW, CREATE, UPDATE, DOWNLOAD, LOGIN), which record, from which IP address, and when. One shared dependency does this so no endpoint forgets. Only admins can read the log. Rows hold ids, never patient names.

Make the table append-only in the database, so a bug or a stolen application login cannot edit or erase history. This SQL has not been run yet; test it once the table exists.

```sql
CREATE FUNCTION audit_logs_no_change() RETURNS trigger AS $$
BEGIN
  RAISE EXCEPTION 'audit_logs is append-only';
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER audit_logs_no_update_delete
  BEFORE UPDATE OR DELETE ON audit_logs
  FOR EACH ROW EXECUTE FUNCTION audit_logs_no_change();

CREATE TRIGGER audit_logs_no_truncate
  BEFORE TRUNCATE ON audit_logs
  FOR EACH STATEMENT EXECUTE FUNCTION audit_logs_no_change();
```

Call it "append-only", not "immutable" or "tamper-proof". A database administrator can still remove the triggers.

## 7. Transport, secrets, and logs

- HTTPS everywhere, including on a local network. `Secure` cookies and PWA install both require it. Browsers make an exception for `localhost` during development.
- Secrets live in `.env`, which `.gitignore` excludes. Commit a `.env.example` with names and no values.
- Never log passwords, tokens, or patient names. The spec's test checklist includes "no PHI in logs" (page 26).
- Use SQLAlchemy queries. Never build SQL by joining strings.
- The web app loads no script from another site at run time, and keeps no patient data in browser storage.

## 8. Data at rest

Two layers. Build the first one for the demo; add the second if time allows.

### Encrypted disk

Run the database and `backend/uploads/` on an encrypted disk (BitLocker on Windows, LUKS on Linux). Docker does not encrypt volumes; an "encrypted volume" means the host disk or partition under it is encrypted. Back up the database and the uploads folder together; one is useless without the other.

### Encrypted name and phone

The spec marks `patients.name` and `patients.phone` as encrypted fields (page 15).

- Encrypt in the application before saving, with AES-256-GCM from the `cryptography` package.
- The key is 32 random bytes from `.env`. Use a fresh random 12-byte nonce for every value and store nonce and ciphertext together.
- Implement it once as a SQLAlchemy column type, so every model and query gets it without extra code.

What it protects against: a stolen database dump or backup shows unreadable names and phone numbers. What it does not protect against: someone who controls the server can read the key from `.env`.

The cost is search. SQL cannot search or index encrypted values, and the spec needs search by name and phone:

- **Phone:** store a second column, `phone_hash`, holding an HMAC-SHA256 of the normalised number made with a separate key. Search by exact match on it.
- **Name:** decrypt in the application and filter there. That is fine for a demo-sized table and too slow for thousands of patients.
- **MRN:** not encrypted, searchable as normal.

Losing the key means losing the data. Keep it out of the repo and back it up separately from the database.

### Supabase's REST API

Supabase serves every table in the `public` schema over its own REST API (`/rest/v1/<table>`) to anyone holding the project's anon key, and that key is meant to be public. That path skips the backend: no login, no roles, no audit log. On 2026-10-09 the anon key alone could read every SarcoScan table there, and insert rows.

The fix: row-level security is switched on for every table, with no policies, so the anon key gets nothing. `upgrade_schema()` in `backend/db.py` does it at every startup on PostgreSQL, so new tables are covered too. The backend is not affected: it owns the tables, and an owner is not bound by row-level security. Never add the anon key to the web app.

## 9. Client shells

- **PWA:** nothing extra. It is the same web app.
- **Tauri (desktop):** the window loads the server URL. Do not add a `remote` entry to any capability file; without one, the remote page cannot call native APIs. Keep the default capability set minimal.
- **Capacitor (mobile):** the web view loads the server URL over HTTPS. Keep `cleartext` off. Add no plugins that are not used.
- **Electron is not used.** It ships a full Node.js runtime next to the page, which needs careful configuration to be safe.

## 10. Privacy

The spec asks for alignment with India's DPDP Act 2023 (page 9):

- Record consent: `patients.consent_given` and `consent_at`. Do not start a screening without it.
- Collect only what the screening needs.
- Use patient data only for screening and the patient's own report.
- Be able to delete a patient and their files on request. The audit log keeps the record that a deletion happened, by id only.

Say "built around DPDP principles". Do not say "DPDP compliant"; nobody has audited it.

For demos and development, use only public dataset images and made-up patients. No real patient data goes into the repo, the demo, or the slides.

## Known gaps

Say these openly if a judge asks. They are in the spec but not in the hackathon build:

- Patient login with "own data only" access
- Separation of data between hospitals
- Key management: the encryption key sits in `.env` on the same server as the data
- Name search by decrypting in the application does not scale
- Text burned into an X-ray image is not removed
- Monitoring and alerting

## Checklist

| # | Item | Status |
|---|---|---|
| 1 | argon2 password hashing | done |
| 2 | Login rate limit | removed on 2026-10-12 for the test build. Planned again before real patient data. |
| 3 | One login token, 7 days, in the browser's `localStorage` | done on 2026-10-12. Replaces the 15-minute token kept in memory. |
| 4 | Refresh token in HttpOnly cookie | removed on 2026-10-12 for the test build. Planned again before real patient data. |
| 5 | UI and API on one origin, CORS closed | done. The web app forwards `/api` to the backend, and the backend has no CORS. |
| 6 | Role dependency on every endpoint | done |
| 7 | Upload size, type, and name checks | done for PNG and JPG |
| 8 | X-rays served only through authenticated endpoints | done on local disk. See item 17. |
| 9 | Audit log dependency | done. Records the browser's address behind the UI's proxy (`client_ip` in `backend/security.py`). |
| 10 | HTTPS on the demo URL | planned |
| 11 | `.env.example` in the repo, `.env` ignored | done |
| 12 | Encrypted disk on the demo server | planned |
| 13 | Test: each role is refused where the table says No | done for the audit log, review, and starting a visit |
| 14 | Append-only triggers on `audit_logs` | done. On PostgreSQL 17, UPDATE, DELETE and TRUNCATE were each refused. |
| 15 | Name and phone encrypted with AES-256-GCM, `phone_hash` for search | done |
| 16 | DICOM uploads converted to PNG, original discarded | later. DICOM uploads are refused for now. |
| 17 | X-rays on Cloudinary are private, read with signed links | in progress: `backend/storage.py` uploads with type `authenticated` and reads with signed URLs; a test checks both with a fake Cloudinary. Done once an upload and image view work on the live site. |
| 18 | The web app loads no third-party script at run time | done. A Tailwind CDN script tag was removed; styles are compiled at build time. |
| 19 | No patient data in browser storage | done. The earlier localStorage store was replaced by calls to the backend. Only the login token is kept there. |
| 21 | A doctor sees only their own patients; admin reads all, writes none | done. Tested: a second doctor gets 404 on the first doctor's patient, visit, result, X-ray and history, and empty lists. |
| 20 | Supabase's REST API cannot reach the tables (row-level security on, no policies) | done. On 2026-10-10, after the deploy, the anon key saw 0 rows in `users`, `patients` and `audit_logs`, and the API kept working. |
