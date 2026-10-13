// One entry point for the whole app, used by the root package.json:
//   node scripts/run.mjs dev     API with auto-reload + web dev server
//   node scripts/run.mjs start   API + production web build (builds first if needed)
//   node scripts/run.mjs test    backend tests
//   node scripts/run.mjs seed    create the three seed users
// Only Node's standard library, so it works on Windows, macOS and Linux with nothing to install.
import { spawn, spawnSync } from "node:child_process";
import { existsSync } from "node:fs";
import { join } from "node:path";
import { createInterface } from "node:readline";
import { fileURLToPath } from "node:url";

const root = fileURLToPath(new URL("..", import.meta.url));
const web = join(root, "frontend", "web");
const mode = process.argv[2] || "dev";
const apiPort = process.env.API_PORT || "8000";
const webPort = process.env.PORT || "3000";
const isWindows = process.platform === "win32";

// The project's virtual environment if `npm run setup` made one, else the Python on PATH.
const python =
  [join(root, ".venv", "Scripts", "python.exe"), join(root, ".venv", "bin", "python")].find(existsSync) ??
  (isWindows ? "python" : "python3");

// The web app forwards /api to this address (frontend/web/next.config.ts). It is read at build time.
const webEnv = { ...process.env, BACKEND_URL: process.env.BACKEND_URL || `http://127.0.0.1:${apiPort}` };

function runOnce(command, args, options = {}) {
  const result = spawnSync(command, args, { cwd: root, stdio: "inherit", shell: isWindows, ...options });
  if (result.status !== 0) process.exit(result.status ?? 1);
}

// Hosts that run only the API (Render sets RENDER=true; anywhere else set ONLY=api): no web app,
// listen on every interface on the port the host gives.
if (mode === "start" && (process.env.RENDER || process.env.ONLY === "api")) {
  const port = process.env.PORT || apiPort;
  runOnce(python, ["-m", "uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", port]);
  process.exit(0);
}

if (mode === "test") runOnce(python, ["-m", "pytest", "backend", ...process.argv.slice(3)]);
else if (mode === "seed") runOnce(python, ["-m", "backend.seed"]);
else if (mode === "dev" || mode === "start") startBoth();
else {
  console.error(`Unknown mode "${mode}". Use dev, start, test or seed.`);
  process.exit(1);
}

function startBoth() {
  if (!existsSync(join(web, "node_modules"))) {
    console.error("frontend/web has no node_modules. Run `npm run setup` first.");
    process.exit(1);
  }
  if (!existsSync(join(root, ".env")) && !process.env.DATABASE_URL) {
    console.error("No .env found. Run `npm run setup` first, or set the variables listed in .env.example.");
    process.exit(1);
  }

  const apiArgs = ["-m", "uvicorn", "backend.main:app", "--port", apiPort];
  if (mode === "dev") apiArgs.push("--reload", "--reload-dir", "backend", "--reload-dir", "ml");

  if (mode === "start" && !existsSync(join(web, ".next", "BUILD_ID"))) {
    console.log("[web] no production build yet, building once...");
    runOnce("npm", ["run", "build"], { cwd: web, env: webEnv });
  }

  const children = [
    launch("api", python, apiArgs, { cwd: root }),
    launch("web", "npm", ["run", mode, "--", "--port", webPort], { cwd: web, env: webEnv }),
  ];
  console.log(`\nSarcoScan ${mode}: web http://localhost:${webPort}  api http://127.0.0.1:${apiPort}/api/v1/health\n`);

  let stopping = false;
  const stopAll = (code) => {
    if (stopping) return;
    stopping = true;
    for (const child of children) kill(child);
    setTimeout(() => process.exit(code), 500);
  };
  for (const child of children) child.on("exit", (code) => stopAll(code ?? 0)); // one dies, both stop
  process.on("SIGINT", () => stopAll(0));
  process.on("SIGTERM", () => stopAll(0));
}

function launch(name, command, args, options) {
  const child = spawn(command, args, { stdio: ["ignore", "pipe", "pipe"], shell: isWindows, ...options });
  for (const stream of [child.stdout, child.stderr]) {
    createInterface({ input: stream }).on("line", (line) => console.log(`[${name}] ${line}`));
  }
  return child;
}

function kill(child) {
  if (child.exitCode !== null) return;
  // With shell: true on Windows the child is cmd.exe; /T also ends the server it started.
  if (isWindows) spawnSync("taskkill", ["/pid", String(child.pid), "/T", "/F"], { stdio: "ignore" });
  else child.kill("SIGTERM");
}
