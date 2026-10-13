"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { registerPatient, type Sex } from "@/lib/store";

export default function NewPatient() {
  const router = useRouter();
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function submit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const f = new FormData(e.currentTarget);
    setBusy(true);
    setError("");
    try {
      const id = await registerPatient({
        mrn: String(f.get("mrn")).trim(),
        name: String(f.get("name")).trim(),
        age: Number(f.get("age")),
        sex: f.get("sex") as Sex,
        heightCm: Number(f.get("heightCm")),
        weightKg: Number(f.get("weightKg")),
        phone: String(f.get("phone")).trim() || undefined,
      });
      router.push(`/patients/${id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not register the patient.");
      setBusy(false);
    }
  }

  return (
    <>
      <h1 className="h1">New patient</h1>
      <button
        type="button"
        className="btn-ghost"
        onClick={() => {
          // Demo helper: a made-up patient. The record number is random so it can be used repeatedly.
          const form = document.querySelector("form")!;
          const sample = { name: "Sample Patient", mrn: `DEMO-${Date.now() % 100000}`, age: "68", sex: "F", heightCm: "154", weightKg: "52" };
          for (const [key, value] of Object.entries(sample)) (form.elements.namedItem(key) as HTMLInputElement).value = value;
          form.querySelector<HTMLInputElement>("input[type=checkbox]")!.checked = true;
        }}
      >
        Fill sample values
      </button>
      <form onSubmit={submit} className="card grid max-w-2xl gap-4 sm:grid-cols-2">
        <label className="label">
          Full name
          <input name="name" required minLength={2} autoComplete="off" className="input" />
        </label>
        <label className="label">
          Hospital record number (MRN)
          <input name="mrn" required maxLength={40} autoComplete="off" className="input" />
        </label>
        <label className="label">
          Age (years)
          <input name="age" type="number" required min={18} max={120} className="input" />
        </label>
        <label className="label">
          Sex
          <select name="sex" required className="input">
            <option value="M">Male</option>
            <option value="F">Female</option>
            <option value="O">Other</option>
          </select>
        </label>
        <label className="label">
          Height (cm)
          <input name="heightCm" type="number" required min={120} max={220} className="input" />
        </label>
        <label className="label">
          Weight (kg)
          <input name="weightKg" type="number" required min={25} max={250} step="0.1" className="input" />
        </label>
        <label className="label sm:col-span-2">
          Phone (optional)
          <input name="phone" type="tel" pattern="[0-9+ -]{7,15}" autoComplete="off" className="input" />
        </label>
        <label className="flex items-start gap-2 text-sm sm:col-span-2">
          <input type="checkbox" required className="mt-1" />
          The patient has agreed to this screening and to their data being stored for it.
        </label>
        {error && (
          <p role="alert" className="text-sm text-red-700 sm:col-span-2">
            {error}
          </p>
        )}
        <button className="btn sm:col-span-2" disabled={busy}>
          {busy ? "Saving..." : "Register patient"}
        </button>
      </form>
    </>
  );
}
