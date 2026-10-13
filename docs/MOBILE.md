# Mobile

Owner: Nidhi.

Status on 2026-10-04: nothing built. Start only after the web UI works on a phone screen. The Capacitor steps below follow the Capacitor docs and have not been run in this repo yet; correct this file when you run them.

There is no separate mobile app to write. The web app in `frontend/web/` is responsive, and the phone opens that same UI. Background in [FRONTEND.md](FRONTEND.md) and [ARCHITECTURE.md](ARCHITECTURE.md).

## Recommended: install the web app on the phone

- Android (Chrome): open the SarcoScan URL, open the menu, choose "Install app".
- iPhone (Safari): open the URL, tap Share, choose "Add to Home Screen".

The app gets a home-screen icon and opens without browser bars. This needs the PWA manifest described in `FRONTEND.md` and HTTPS on the server, and nothing else.

## Optional: an APK with Capacitor (demo only)

Build this only if an installable APK file is required.

It is a shell that opens the server URL through Capacitor's `server.url` setting. Capacitor's own documentation says of that setting: "This is intended for use with live-reload servers. This is not intended for use in production." So this is acceptable for a hackathon demo and not for a released app.

Needed on the build machine: Android Studio with the Android SDK, and the JDK version Capacitor asks for. Check https://capacitorjs.com/docs/getting-started/environment-setup first.

```
mkdir frontend/android-shell
cd frontend/android-shell
npm init -y
npm install @capacitor/core @capacitor/cli @capacitor/android
npx cap init SarcoScan com.codesharks.sarcoscan --web-dir www
```

Create `www/index.html` with a short "Cannot reach the SarcoScan server" message. Capacitor needs the file to exist; it is shown only if the server URL fails to load.

```
npx cap add android
```

Then set the server URL in the Capacitor config file that `cap init` created:

```json
{
  "appId": "com.codesharks.sarcoscan",
  "appName": "SarcoScan",
  "webDir": "www",
  "server": { "url": "https://your-server.example" }
}
```

```
npx cap sync
npx cap open android     # opens Android Studio; build the APK from there
```

## Security rules for this shell

- Use an `https://` server URL. Leave `cleartext` off.
- Add no Capacitor plugins. The shell only shows a web page.
- Do not commit build output or the APK.

## If a store-ready app is ever needed

Bundle a static build of the UI inside the app instead of loading a URL. That requires Next.js static export, which has limits (for example it does not support `proxy.ts`), and a different login setup because the app and the API would no longer share an origin. Plan it as its own piece of work.
