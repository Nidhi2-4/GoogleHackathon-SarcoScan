# Desktop shell

Owner: Nidhi, with Anish for the build (Rust is already installed on Anish's machine).

Status on 2026-10-04: nothing built. Start only after the web UI works. The steps below follow the Tauri v2 docs and have not been run in this repo yet; correct this file when you run them.

The plan is a Tauri shell: a small desktop program whose window opens the SarcoScan web UI from the server. No UI code lives here. Background in [FRONTEND.md](FRONTEND.md) and [ARCHITECTURE.md](ARCHITECTURE.md).

## Try this first: install the web app

In Chrome or Edge, open the SarcoScan URL and click the install icon in the address bar. The app gets its own window and taskbar icon. This needs the PWA manifest described in `FRONTEND.md` and nothing else.

Build the Tauri shell only if an `.exe` installer is required.

## Building the Tauri shell

Needed on the build machine (Windows): Rust, Microsoft C++ Build Tools, and WebView2, which ships with Windows 11. Full list: https://v2.tauri.app/start/prerequisites/

```
mkdir frontend/desktop
cd frontend/desktop
npm init -y
npm install -D @tauri-apps/cli@latest
npx tauri init
```

`tauri init` asks for the app name, window title, and where the web assets are. Then edit `src-tauri/tauri.conf.json` so the window loads the server instead of local files:

```json
{
  "build": {
    "frontendDist": "https://your-server.example",
    "devUrl": "http://localhost:3000"
  }
}
```

`frontendDist` may be a remote URL. With a URL, no assets are bundled; the app loads that address.

```
npx tauri dev      # opens devUrl, for testing against a local web app
npx tauri build    # creates the installer under src-tauri/target/release/bundle/
```

## Security rules for this shell

- Do not add a `remote` entry to any file in `src-tauri/capabilities/`. It is unset by default, which means the page loaded from the server cannot call native APIs. Adding it would give a web page access to the local system.
- Add no Tauri plugins. The shell only shows a web page.
- Point `frontendDist` at an `https://` address.
- Do not commit `src-tauri/target/`. `.gitignore` already excludes `target/`.

## Why Tauri and not Electron

Tauri uses the operating system's web view and gives the page no Node.js access. Native features are off unless allowed one by one. Electron ships its own browser and a Node.js runtime next to the page, which is larger and needs careful configuration to be safe.
