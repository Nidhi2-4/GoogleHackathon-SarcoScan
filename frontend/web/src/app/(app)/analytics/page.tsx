"use client";

import { STAGE, TIER, finalStage, useStore } from "@/lib/store";

function Bars({ title, rows, total }: { title: string; rows: [string, number][]; total: number }) {
  return (
    <section className="card space-y-2">
      <h2 className="h2">{title}</h2>
      {rows.map(([label, n]) => (
        <label key={label} className="grid grid-cols-[9rem_1fr_2rem] items-center gap-3 text-sm">
          {label}
          <progress value={n} max={total || 1} className="h-2 w-full accent-[#0284c7]" />
          {n}
        </label>
      ))}
    </section>
  );
}

export default function Analytics() {
  const { screenings } = useStore();
  const total = screenings.length;
  const lowGrip = screenings.filter((s) => s.bestGrip !== null && s.bestGrip < s.gripCutoff).length;

  return (
    <>
      <h1 className="h1">Analytics</h1>
      <p className="text-sm text-[#64748b]">Across {total} screenings.</p>
      <div className="grid gap-4 lg:grid-cols-2">
        <Bars
          title="Sarcopenia stage"
          total={total}
          rows={Object.entries(STAGE).map(([k, v]) => [v.label, screenings.filter((s) => finalStage(s) === k).length])}
        />
        <Bars
          title="Osteoporosis risk tier"
          total={total}
          rows={Object.entries(TIER).map(([k, v]) => [v.label, screenings.filter((s) => s.osteoTier === k).length])}
        />
        <Bars
          title="Workflow"
          total={total}
          rows={[
            ["Low grip strength", lowGrip],
            ["Doctor overrides", screenings.filter((s) => s.override).length],
            ["Finalized", screenings.filter((s) => s.finalized).length],
          ]}
        />
      </div>
    </>
  );
}
