# Frontend: web, mobile, desktop

Owner: Nidhi. Last updated: 2026-10-04.

Status: the web app in `frontend/web/` is built and talks to the backend. It builds cleanly, and the whole screening flow was run through it against a test backend. Anish clicked through it in a browser on 2026-10-04, including the PDF download with the X-ray. No automated browser check exists.

One UI serves all three platforms. Phones and desktops open the same web app. See "Web, mobile, and desktop" in `ARCHITECTURE.md` for the reasoning.

## Running it

```
cd frontend/web
npm install
npm run dev
```

The app is at http://localhost:3000. The backend must be running on port 8000 (see `backend/README.md`), or every page shows a sign-in error.

`npm run build` must pass before a commit. `npx eslint src` should show no errors.

## How the app is put together

```
frontend/web/
├── next.config.ts            forwards /api to the backend
├── src/app/
│   ├── (site)/               public pages: home, about, privacy, terms
│   ├── login/                sign in
│   └── (app)/                the clinic app, behind sign-in
│       ├── dashboard, patients, patients/new, patients/[id]
│       ├── patients/[id]/screen      the screening wizard
│       ├── reports, reports/[id]     report, doctor review, PDF
│       └── studies, analytics, admin, settings
├── src/components/app.tsx    badges, tables, Findings, XrayImage, ModelStatus
└── src/lib/
    ├── api.ts                calls to the backend, login token, refresh
    ├── store.ts              the data every page reads, and the actions that change it
    └── pdfReport.ts          the PDF report: findings on page 1, the X-ray on page 2
```

### Data flow

- Every page reads from `useStore()` in `store.ts`. The store holds what the backend returned: the user, patients, analysed visits, the audit log (admins only), and whether a model is connected.
- Pages change data only through the store's actions (`signIn`, `registerPatient`, `saveInputs`, `uploadXray`, `runAnalysis`, `reviewScreening`). Each action calls the backend and then reloads the store.
- Nothing about a patient is written to `localStorage` or any other browser storage. A page reload fetches everything again.
- The store's types use short names (`heightCm`, `M`/`F`/`O`); `store.ts` converts to and from the backend's names in one place.

### Talking to the backend

The browser never calls the backend's address directly. Next.js forwards `/api` to it (`next.config.ts`), so the UI and the API share one origin. This keeps CORS closed and makes the login cookie work (`SECURITY.md`, section 3).

`BACKEND_URL` is read when the app is built. Set it before `npm run build` if the backend is not at `http://127.0.0.1:8000`.

In the UI, always call relative paths through `api.ts`. Never hard-code a host or port.

### Login on the client

1. `signIn` posts to `/api/v1/auth/login` and keeps the access token in a variable in `api.ts`. It is never put in browser storage.
2. The backend sets the refresh cookie. The UI never reads or writes it.
3. On a 401, `api.ts` calls refresh once and repeats the request. Calls made at the same moment share one refresh, because the backend treats a second use of an old refresh token as theft.
4. After a page reload the token in memory is gone, so the store calls refresh at start.
5. Menu items a role cannot use are hidden. That is for convenience; the backend still refuses the call.

## The PDF report

`pdfReport.ts` builds it in the browser from what the backend stored. Page 1 has the letterhead (hospital on the left, SarcoScan on the right), the patient box, the two results, the measured values next to their cutoffs, the suggested action, the doctor's note, and who screened and reviewed. Page 2 has the X-ray.

The hospital name and address are typed on the sign-in page and remembered in that browser (`localStorage`; they are a device setting, not patient data). Without a name the report says "Demo Hospital". The seed-account buttons fill in a made-up hospital. There is no hospital logo, only the name.

## The screening flow

1. Clinical inputs (all optional): the five SARC-F questions (the score is added up on screen; all five or none), 5-chair-stand time, calf circumference, waist, upper arm circumference, and a medical-history checklist. **Fill sample values** fills every step with made-up values and the sample X-ray.
2. Handgrip: three trials per hand. The best value and the cutoff show while typing.
3. X-ray: choose a JPG or PNG, then press **Run screening**. That one button saves the inputs, uploads the image, runs the server's quality check, and runs the analysis. Each stage is named on screen while it happens. If the image fails the check, the reason is shown and another image can be chosen.
4. Results: stage, risk, measured values next to cutoffs, the X-ray, **Download PDF report**, and a link to the report page.
5. Report page: the doctor agrees or overrides the stage with a reason. Print and Download PDF are here too.

Results do not change live as inputs change. A screening is a saved, audited event: the inputs are sent, the server decides, and the result is stored. Only the handgrip best-value line updates while typing.

### When no model is connected

The backend says whether `ml/predict.py` exists (`/api/v1/health`). The sidebar and Settings show "AI model: connected" or "not connected".

Without a model a screening still runs and shows everything that is real: the stage from the AWGS 2019 rules, grip against its cutoff, chair-stand time, SARC-F, calf circumference, BMI, and the X-ray. Osteoporosis risk, the ratios, and the overlay say "Not available". No value is estimated in the browser.

## Rules

- **Show only what the backend sent.** No formulas that produce probabilities or measurements in the UI.
- **No third-party scripts at run time.** Tailwind is compiled at build time by `@tailwindcss/postcss`. Do not add a CDN script tag: it breaks the app on a network without internet and runs someone else's code next to patient data.
- **Do not add a `proxy.ts`** (the new name for `middleware.ts` in Next.js 16). With one present, Next.js keeps only the first 10 MB of a request body by default, and X-rays can be 50 MB.
- Check any Next.js API in `frontend/web/node_modules/next/dist/docs/` before using it; version 16 differs from older tutorials.
- Risk is never shown by colour alone; the word is always there.
- Every results screen and report carries the line that this is a screening aid, not a diagnosis.

## Phones and desktops

| Stage | What it gives | Status |
|---|---|---|
| Responsive web app | Works in desktop and phone browsers | done; test each screen on a real phone |
| PWA manifest (`src/app/manifest.ts` plus two icons) | "Install" on phones and desktops: own icon, own window. Needs HTTPS. | planned |
| Desktop installer | See [DESKTOP.md](DESKTOP.md) (Tauri) | planned, optional |
| Android APK | See [MOBILE.md](MOBILE.md) (Capacitor, demo only) | planned, optional |

`frontend/mobile/` holds an untouched Expo template. A separate React Native app is not planned: the spec wanted one for the Bluetooth dynamometer, and spec version 2 moved handgrip to manual entry.

## Design reference

A design canvas with 14 screens: https://claude.ai/artifact/QD73sqhXZV5EaatPSguTXa

It is private to Anish until he shares it from the page's Share menu. The web app has its own look (blue and white; the palette is the `:root` block in `src/app/globals.css`, and the clinic app's shared classes `.card`, `.btn`, `.input`, `.table` sit at the end of that file); the canvas is a reference for layout ideas, the risk-level bars, and the phone screens. All patients and values on it are made up.

## The spec document and the deck

Nidhi also owns the spec PDF. Two fixes are pending:

- Add the desktop app. The spec does not mention it anywhere.
- Version 2 changed must-have item 7 to manual handgrip entry, but 13 other lines still mention Bluetooth.

Keep one spec PDF in `docs/`.
