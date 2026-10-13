"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { signIn, useStore } from "@/lib/store";

// Local demo only: read from .env.local, which is never committed. Empty in any build without it.
const DEMO_PASSWORDS: Record<string, string> = JSON.parse(process.env.NEXT_PUBLIC_DEMO_LOGINS || "{}");

export default function Login() {
  const router = useRouter();
  const { ready, user } = useStore();
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    if (ready && user) router.replace("/dashboard");
  }, [ready, user, router]);

  // The hospital name and address go on the PDF letterhead. They are a setting of this device,
  // not patient data, so they are remembered in the browser.
  useEffect(() => {
    const form = document.querySelector("form")!;
    for (const key of ["hospitalName", "hospitalAddress"]) {
      (form.elements.namedItem(key) as HTMLInputElement).value = localStorage.getItem(key) ?? "";
    }
  }, []);

  async function submit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const data = new FormData(e.currentTarget);
    for (const key of ["hospitalName", "hospitalAddress"]) localStorage.setItem(key, String(data.get(key)).trim());
    setBusy(true);
    setError("");
    try {
      await signIn(String(data.get("email")).trim(), String(data.get("password")));
      router.replace("/dashboard");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not sign in.");
      setBusy(false);
    }
  }

  return (
    <main className="m-auto w-full max-w-sm p-4">
      <h1 className="h1 text-center">SarcoScan</h1>
      <p className="mt-1 mb-6 text-center text-sm text-[#64748b]">Sign in to the clinic dashboard</p>
      <form onSubmit={submit} className="card space-y-4">
        <label className="label">
          Email
          <input name="email" type="email" required autoFocus autoComplete="username" className="input" />
        </label>
        <label className="label">
          Password
          <input name="password" type="password" required autoComplete="current-password" className="input" />
        </label>
        <label className="label">
          Hospital name (shown on reports)
          <input name="hospitalName" maxLength={60} autoComplete="organization" className="input" />
        </label>
        <label className="label">
          Hospital address (optional)
          <input name="hospitalAddress" maxLength={80} autoComplete="off" className="input" />
        </label>
        {error && (
          <p role="alert" className="text-sm text-red-700">
            {error}
          </p>
        )}
        <button className="btn w-full" disabled={busy}>
          {busy ? "Signing in..." : "Sign in"}
        </button>
      </form>
      <div className="mt-4 flex flex-wrap items-center gap-2 text-xs text-[#64748b]">
        Seed accounts:
        {["technician", "doctor", "admin"].map((role) => (
          <button
            key={role}
            type="button"
            className="btn-ghost px-2 py-1 text-xs capitalize"
            onClick={(e) => {
              const form = e.currentTarget.closest("main")!.querySelector("form")!;
              (form.elements.namedItem("email") as HTMLInputElement).value = `${role}@sarcoscan.local`;
              const password = form.elements.namedItem("password") as HTMLInputElement;
              password.value = DEMO_PASSWORDS[role] ?? "";
              // Made-up hospital for demos; kept if something is already typed.
              const fill = (key: string, value: string) => {
                const input = form.elements.namedItem(key) as HTMLInputElement;
                if (!input.value) input.value = value;
              };
              fill("hospitalName", "CodeSharks Demo Hospital");
              fill("hospitalAddress", "Orthopaedics OPD, Jaipur, Rajasthan");
              password.focus();
            }}
          >
            {role}
          </button>
        ))}
      </div>
      <p className="mt-4 text-xs text-[#64748b]">Accounts are created by the hospital admin.</p>
      <Link href="/" className="mt-4 block text-center text-sm underline">
        Back to home
      </Link>
    </main>
  );
}
