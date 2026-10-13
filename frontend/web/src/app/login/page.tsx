"use client";

import Image from "next/image";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { DEMO_ACCOUNTS, DEMO_PASSWORD } from "@/lib/demo";
import { signIn, signUp, useStore } from "@/lib/store";

export default function Login() {
  const router = useRouter();
  const { ready, user } = useStore();
  const [creating, setCreating] = useState(false); // false: sign in, true: create an account
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [show, setShow] = useState(false);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    if (ready && user) router.replace("/dashboard");
  }, [ready, user, router]);

  async function enter(action: () => Promise<void>) {
    setBusy(true);
    setError("");
    try {
      await action();
      router.replace("/dashboard");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not sign in.");
      setBusy(false);
    }
  }

  function submit(e: React.FormEvent) {
    e.preventDefault();
    enter(() => (creating ? signUp(name.trim(), email.trim(), password) : signIn(email.trim(), password)));
  }

  return (
    <main className="m-auto w-full max-w-sm p-4">
      <div className="mb-6 flex flex-col items-center gap-2 text-center">
        <Image src="/logo-mark.png" alt="" width={40} height={50} priority />
        <h1 className="h1">{creating ? "Create a SarcoScan account" : "Sign in to SarcoScan"}</h1>
        <p className="text-sm text-[#64748b]">
          {creating ? "A doctor account. Test build: use made-up patients only." : "For doctors and hospital admins."}
        </p>
      </div>

      <form onSubmit={submit} className="card space-y-4">
        {creating && (
          <label className="label">
            Full name
            <input
              required
              minLength={2}
              maxLength={120}
              autoComplete="name"
              className="input"
              value={name}
              onChange={(e) => setName(e.target.value)}
            />
          </label>
        )}
        <label className="label">
          Email
          <input
            type="email"
            required
            autoFocus
            autoComplete="username"
            placeholder="name@hospital.org"
            className="input"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />
        </label>
        <div>
          <label className="label" htmlFor="password">
            Password
          </label>
          <div className="relative">
            <input
              id="password"
              type={show ? "text" : "password"}
              required
              autoComplete={creating ? "new-password" : "current-password"}
              className="input pr-16"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
            <button
              type="button"
              aria-pressed={show}
              className="absolute inset-y-0 right-0 mt-1 px-3 text-xs font-semibold text-[#0369a1]"
              onClick={() => setShow(!show)}
            >
              {show ? "Hide" : "Show"}
            </button>
          </div>
        </div>
        {error && (
          <p role="alert" className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">
            {error}
          </p>
        )}
        <button className="btn w-full" disabled={busy}>
          {busy ? "Please wait..." : creating ? "Create account" : "Sign in"}
        </button>
        <button
          type="button"
          className="w-full text-center text-sm underline"
          onClick={() => {
            setCreating(!creating);
            setError("");
          }}
        >
          {creating ? "I already have an account" : "New here? Create an account"}
        </button>
      </form>

      <section className="card mt-4 space-y-3 text-sm">
        <div>
          <h2 className="font-semibold">Try the demo</h2>
          <p className="text-xs text-[#64748b]">
            A sample doctor account with made-up patients. Password: <code>{DEMO_PASSWORD}</code>
          </p>
        </div>
        {DEMO_ACCOUNTS.map((account) => (
          <div key={account.email} className="flex items-center justify-between gap-3">
            <div className="min-w-0">
              <p className="font-medium">{account.label}</p>
              <p className="break-all text-xs text-[#64748b]">{account.email}</p>
            </div>
            <button
              type="button"
              className="btn-ghost shrink-0 px-3 py-1 text-xs"
              disabled={busy}
              onClick={() => enter(() => signIn(account.email, DEMO_PASSWORD))}
            >
              Sign in as {account.label}
            </button>
          </div>
        ))}
      </section>

      <Link href="/" className="mt-4 block text-center text-sm underline">
        Back to home
      </Link>
    </main>
  );
}
