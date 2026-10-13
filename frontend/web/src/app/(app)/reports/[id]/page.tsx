"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useState } from "react";
import { Findings, StageBadge, XrayImage } from "@/components/app";
import { downloadReport } from "@/lib/pdfReport";
import { SEX_LABEL, STAGE, finalStage, reviewScreening, useStore, type Stage } from "@/lib/store";

export default function Report() {
  const { id } = useParams<{ id: string }>();
  const { patients, screenings, user } = useStore();
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const s = screenings.find((x) => x.id === id);
  const p = patients.find((x) => x.id === s?.patientId);
  if (!s || !p) return <p>Report not found.</p>;

  /** Run one action against the backend, showing why it failed if it does. */
  async function act(action: () => Promise<void>) {
    setBusy(true);
    setError("");
    try {
      await action();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong. Try again.");
    } finally {
      setBusy(false);
    }
  }

  function override(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const f = new FormData(e.currentTarget);
    act(() => reviewScreening(s!.id, f.get("stage") as Stage, String(f.get("reason")).trim()));
  }

  return (
    <>
      <header className="flex flex-wrap items-center justify-between gap-3">
        <h1 className="h1">SarcoScan screening report</h1>
        <div className="no-print flex flex-wrap gap-2">
          <button className="btn-ghost" onClick={() => window.print()}>
            Print
          </button>
          <button className="btn" disabled={busy} onClick={() => act(() => downloadReport(p, s))}>
            Download PDF
          </button>
        </div>
      </header>

      <dl className="card grid grid-cols-2 gap-4 text-sm sm:grid-cols-4">
        {[
          ["Patient", `${p.name} (${p.mrn})`],
          ["Age / sex", `${p.age} / ${SEX_LABEL[p.sex]}`],
          ["Screening date", s.date],
          ["Screened by", s.by],
          ["Status", s.finalized ? `Reviewed by ${s.reviewedBy}` : "Pending doctor review"],
        ].map(([k, v]) => (
          <div key={k}>
            <dt className="text-xs text-[#64748b]">{k}</dt>
            <dd className="font-semibold break-words">{v}</dd>
          </div>
        ))}
      </dl>

      <Findings patient={p} r={s} stage={finalStage(s)} />

      {s.xrayId && (
        <section className="card">
          <h2 className="h2">Knee X-ray</h2>
          <XrayImage xrayId={s.xrayId} hasOverlay={s.hasOverlay} />
        </section>
      )}

      {s.override && (
        <p className="card text-sm">
          <strong>Doctor override by {s.override.by}:</strong> the system&apos;s stage was <StageBadge stage={s.stage} />,
          changed to <StageBadge stage={s.override.stage} />. Reason: {s.override.reason}
        </p>
      )}

      {error && (
        <p role="alert" className="no-print text-sm text-red-700">
          {error}
        </p>
      )}

      {user?.role === "doctor" && !s.finalized && (
        <form onSubmit={override} className="card no-print grid gap-4 sm:grid-cols-[auto_1fr_auto_auto] sm:items-end">
          <label className="label">
            Override stage
            <select name="stage" defaultValue={s.stage} className="input">
              {Object.entries(STAGE).map(([k, v]) => (
                <option key={k} value={k}>
                  {v.label}
                </option>
              ))}
            </select>
          </label>
          <label className="label">
            Reason (required to override)
            <input name="reason" required minLength={5} maxLength={2000} className="input" />
          </label>
          <button className="btn-ghost" disabled={busy}>
            Save override
          </button>
          <button type="button" className="btn" disabled={busy} onClick={() => act(() => reviewScreening(s.id))}>
            Agree and finalize
          </button>
        </form>
      )}

      <Link href={`/patients/${p.id}`} className="no-print text-sm underline">
        Back to patient
      </Link>
    </>
  );
}
