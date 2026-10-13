// First-time setup for a fresh clone: `npm run setup`. Safe to run again; it skips what is done.
//   1. Python virtual environment in .venv and the backend's packages
//   2. The web app's packages
//   3. A local .env (SQLite, fresh random keys, random seed passwords) if there is none
//   4. The two seed users (admin, doctor)
import { spawnSync } from "node:child_process";
import { randomBytes } from "node:crypto";
import { existsSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import { fileURLToPath } from "node:url";

const root = fileURLToPath(new URL("..", import.meta.url));
const isWindows = process.platform === "win32";
const systemPython = isWindows ? "python" : "python3";
const venvPython = join(root, ".venv", isWindows ? "Scripts" : "bin", isWindows ? "python.exe" : "python");

function step(title, command, args, cwd = root, { canFail = false } = {}) {
  console.log(`\n== ${title}`);
  const result = spawnSync(command, args, { cwd, stdio: "inherit", shell: isWindows });
  if (result.status === 0) return true;
  if (canFail) return false;
  console.error(`\nFailed: ${title}. Fix the error above and run \`npm run setup\` again.`);
  process.exit(result.status ?? 1);
}

if (!existsSync(venvPython)) step("Create .venv", systemPython, ["-m", "venv", ".venv"]);
const pipArgs = ["install", "-r", join("backend", "requirements.txt")];
const installed = step("Install backend packages (first time takes a few minutes: torch)", venvPython,
  ["-m", "pip", ...pipArgs], root, { canFail: true });
if (!installed) {
  // A new venv ships an old pip, which fails on some networks with a certificate error.
  // The system pip (22.3 or newer) can install into the venv instead.
  step("Retry with the system pip", systemPython, ["-m", "pip", "--python", venvPython, ...pipArgs]);
}
step("Install web packages", "npm", ["ci"], join(root, "frontend", "web"));

const envPath = join(root, ".env");
if (existsSync(envPath)) {
  console.log("\n== .env already exists, left as it is");
} else {
  const key = () => randomBytes(32).toString("base64");
  const password = () => randomBytes(9).toString("base64url"); // 12 characters
  const seeds = { SEED_ADMIN_PASSWORD: password(), SEED_DOCTOR_PASSWORD: password() };
  const lines = [
    "# Local development, written by `npm run setup`. Everything stays on this machine.",
    "# For hosted values see .env.example and docs/DEPLOY.md. Never commit this file.",
    "DATABASE_URL=sqlite:///./sarcoscan.db?check_same_thread=false",
    `JWT_SECRET=${randomBytes(48).toString("base64url")}`,
    `FIELD_KEY=${key()}`,
    `HASH_KEY=${key()}`,
    "STORAGE_BACKEND=local",
    ...Object.entries(seeds).map(([name, value]) => `${name}=${value}`),
  ];
  writeFileSync(envPath, lines.join("\n") + "\n");
  console.log("\n== Wrote .env for local use. Seed logins (also in .env):");
  for (const role of ["admin", "doctor"]) {
    console.log(`   ${role}@sarcoscan.local  ${seeds[`SEED_${role.toUpperCase()}_PASSWORD`]}`);
  }
}

step("Create seed users", venvPython, ["-m", "backend.seed"]);
console.log("\nDone. Start everything with: npm run dev");
