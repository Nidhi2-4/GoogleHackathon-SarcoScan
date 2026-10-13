---
name: sarcoscan-frontend
description: Working rules for the SarcoScan UI and its shells (Next.js 16 app in frontend/web/, responsive screens, calling the API through /api, login token handling, PWA manifest, Tauri desktop shell, Capacitor mobile shell). Use whenever you create or change anything under frontend/.
---

# SarcoScan frontend

Read `docs/FRONTEND.md` first. It has the setup command, the screen list, the API proxy config, the login flow, and the PWA and shell steps. This skill is the short list of rules to follow while working.

Owner of these folders: Nidhi. If a task needs a change outside `frontend/`, tell the user instead of making it quietly.

## Next.js 16

`frontend/web/` is Next.js 16 with the App Router. It differs from older versions.

- Read `frontend/web/AGENTS.md` and follow it. Check any Next.js API in `frontend/web/node_modules/next/dist/docs/` before using it. Do not rely on memory of older versions.
- `middleware.ts` is now `proxy.ts`.
- Do not add a `proxy.ts`. With one present, Next.js keeps only the first 10 MB of a request body by default, and X-ray uploads can be 50 MB. If one is truly needed, set `experimental.proxyClientMaxBodySize` to `'50mb'` and test a large upload.

## Rules

0. **Data comes from the backend.** Pages read `useStore()` and change data only through the actions in `src/lib/store.ts`. No patient data in browser storage, no formulas that produce results in the UI, no scripts loaded from another site.
1. **One UI.** Every screen is built once in `frontend/web/`. Never build a second version of a screen for mobile or desktop. Phones and desktops open the same web app.
2. **Phone width first.** Each screen must work on a phone before it is called done. Touch targets at least 44 px.
3. **Relative API paths.** Call `/api/v1/...`. Never hard-code the backend's host or port. The forwarding rule lives in `frontend/web/next.config.ts`.
4. **Token handling.** Only `src/lib/api.ts` touches the login token. It is kept in `localStorage` while this is a test build (`docs/SECURITY.md`, section 2). On 401, delete it and go to login.
5. **The UI is not the security boundary.** Hide what a role cannot use, and expect the backend to refuse it anyway. Never decide access from data the user can edit.
6. **Show only what the backend sent.** No made-up percentages, no placeholder accuracy figures. When the sarcopenia stage has no probability, show the stage and the inputs next to their cutoffs.
7. **Risk is never colour alone.** Always show the word (Low, Moderate, High; None, Possible, Probable, Severe) next to the colour.
8. **Never render user text as HTML.** No `dangerouslySetInnerHTML` with data from the API.
9. **Screening-aid disclaimer** on the results screen and the report.
10. **Add a package only when a screen needs it.** `fetch` is built in. Recharts is expected for the trend graph.

## Shells

- PWA first: `frontend/web/src/app/manifest.ts` plus two icons in `frontend/web/public/`. Needs HTTPS.
- Desktop: follow `docs/DESKTOP.md`. Never add a `remote` entry to a Tauri capability file, and add no plugins.
- Mobile: follow `docs/MOBILE.md`. HTTPS server URL only, `cleartext` off, no plugins.
- Out of scope unless a teammate asks: React Native, Expo, Electron, Bluetooth.

## Before you say it is done

- Open the screen at phone width and at desktop width.
- Run `npm run lint` and `npm run build` in `frontend/web/`.
- Update the screen's status in `docs/FRONTEND.md` and tick the box in `docs/PLAN.md`.
- If you ran the shell steps, correct `docs/DESKTOP.md` or `docs/MOBILE.md` to match what actually worked.
