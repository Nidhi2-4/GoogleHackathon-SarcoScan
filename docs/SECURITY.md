# Security

Owner: Anish. Last updated: 2026-10-04.

Status: the backend controls are built and tested, and the web app uses them. The audit triggers were checked on PostgreSQL. Nothing has run over HTTPS yet. The checklist at the bottom tracks each item; update it as items change.

## The main idea

Security comes from the backend, not from the platform. Web, mobile, and desktop all talk to the same API. If the API checks every request properly, all three are protected. If it does not, no client can make up for it. A desktop app is not safer than a web app by itself.

So the backend must do four things on every request: know who is calling, check that their role allows the action, validate what they sent, and record what they did.

## 1. Passwords and login

- Hash passwords with argon2 (for example the `argon2-cffi` or `pwdlib` package). Never store, log, or return a plain password.
- Rate-limit `/auth/login`, for example 5 attempts per minute per IP address. This slows password guessing.
- Give the same error for "no such email" and "wrong password", so the login form does not reveal which emails exist.
- A seed script creates the first admin, doctor, and technician. Their passwords come from `.env`, not from the code.

## 2. Tokens

Two tokens, as in the spec (page 21):

| Token | Lifetime | Where the client keeps it | Why |
|---|---|---|---|
| Access token (JWT with user id and role) | 15 minutes | In JavaScript memory only. Not in localStorage. | If it leaks, it expires quickly. |
| Refresh token | 7 days | Cookie with `HttpOnly`, `Secure`, `SameSite=Strict`, `Path=/api/v1/auth` | JavaScript cannot read an HttpOnly cookie, so a script injected into the page cannot steal it. |

Rules:

- The database stores only a hash of the refresh token.
- Every call to `/auth/refresh` issues a new refresh token and revokes the old one (rotation).
- If a revoked refresh token is used again, treat it as theft: revoke all of that user's refresh tokens.
- Logout revokes the refresh token and clears the cookie.
- Sign access tokens with a long random secret from `.env`.

`SameSite=Strict` stops other websites from triggering the refresh endpoint with the user's cookie. All other endpoints use the `Authorization` header, which a foreign site cannot set.

## 3. One origin for UI and API

Serve the UI and the API from the same origin: the web app forwards `/api` to the backend (see `FRONTEND.md`). Then:

- The refresh cookie is a first-party cookie and `SameSite=Strict` works.
- CORS stays closed. Do not add `allow_origins=["*"]`.
- The mobile and desktop shells open the same URL, so they use exactly the same login flow.

## 4. Roles

The server checks the role on every endpoint with one shared dependency. From the spec (page 21):

| Action | Technician | Doctor | Admin | Patient |
|---|---|---|---|---|
| Register patient | Yes | Yes | Yes | No |
| Run screening | Yes | Yes | No | No |
| View results | Yes | Yes | Yes | Own only |
| Override or review | No | Yes | No | No |
| Generate report | Yes | Yes | No | No |
| Manage users and devices | No | No | Yes | No |
| View audit logs | No | No | Yes | No |

The role comes from the verified access token, never from the request body or a query parameter. The UI may hide buttons a role cannot use, but that is for convenience only.

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

### If X-rays are copied to a cloud store

An X-ray is patient data wherever it sits. If files are mirrored to Cloudinary or a similar service for a hosted demo:

- Upload them as private or authenticated assets. A default upload can be opened by anyone who has the link, with no login.
- Give clients only signed links that expire, or keep serving the file through the authenticated endpoints.
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
| 2 | Login rate limit, 5 a minute per address | done. Kept in memory, so it counts per server process. Counts per browser address, read from the proxy's `X-Forwarded-For` (trusted only from this machine). |
| 3 | Access token, 15 minutes, memory only | done. The web app keeps it in a variable in `api.ts`, never in browser storage. |
| 4 | Refresh token in HttpOnly cookie, hashed in database, rotated, reuse signs the user out everywhere | done |
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
| 17 | Cloud copies of X-rays are private, with signed links | done for the upload: `backend/storage.py` uploads with type `authenticated`, so no public URL exists. Not exercised against a real Cloudinary account. The app never serves from Cloudinary; images are read from local disk through the authenticated endpoints. |
| 18 | The web app loads no third-party script at run time | done. A Tailwind CDN script tag was removed; styles are compiled at build time. |
| 19 | No patient data in browser storage | done. The earlier localStorage store was replaced by calls to the backend. |
