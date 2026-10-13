"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { ScreeningTable, byDateDesc } from "@/components/app";
import { SEX_LABEL, bmi, gripCutoff, useStore } from "@/lib/store";

/** Best grip across visits, with the AWGS cutoff as a dashed line. */
function GripTrend({ values, cutoff }: { values: number[]; cutoff: number }) {
  const max = Math.max(...values, cutoff) * 1.2;
  const x = (i: number) => (values.length === 1 ? 150 : 15 + (i * 270) / (values.length - 1));
  const y = (v: number) => 100 - (v / max) * 90;
  return (
    <svg viewBox="0 0 300 105" role="img" aria-label="Best grip strength across visits" className="w-full max-w-xl">
      <line x1="0" x2="300" y1={y(cutoff)} y2={y(cutoff)} stroke="#b91c1c" strokeDasharray="4 3" strokeWidth="0.7" />
      <text x="2" y={y(cutoff) - 2} fontSize="6" fill="#b91c1c">
        cutoff {cutoff} kg
      </text>
      <polyline points={values.map((v, i) => `${x(i)},${y(v)}`).join(" ")} fill="none" stroke="#0284c7" strokeWidth="1.5" />
      {values.map((v, i) => (
        <text key={i} x={x(i)} y={y(v) - 3} fontSize="6" textAnchor="middle">
          {v}
        </text>
      ))}
    </svg>
  );
}

export default function PatientProfile() {
  const { id } = useParams<{ id: string }>();
  const { patients, screenings } = useStore();
  const p = patients.find((x) => x.id === id);
  if (!p) return <p>Patient not found.</p>;
  const visits = screenings.filter((s) => s.patientId === id).sort(byDateDesc);
  const grips = [...visits].reverse().flatMap((s) => (s.bestGrip === null ? [] : [s.bestGrip]));

  return (
    <>
      <header className="flex flex-wrap items-center justify-between gap-3">
        <h1 className="h1">
          {p.name} <small className="text-sm font-normal text-[#64748b]">{p.mrn}</small>
        </h1>
        <Link href={`/patients/${id}/screen`} className="btn">
          Start screening
        </Link>
      </header>

      <dl className="card grid grid-cols-2 gap-4 text-sm sm:grid-cols-5">
        {[
          ["Age", `${p.age} years`],
          ["Sex", SEX_LABEL[p.sex]],
          ["Height / weight", `${p.heightCm} cm / ${p.weightKg} kg`],
          ["BMI", bmi(p).toFixed(1)],
          ["Phone", p.phone ?? "Not given"],
        ].map(([k, v]) => (
          <div key={k}>
            <dt className="text-xs text-[#64748b]">{k}</dt>
            <dd className="font-semibold">{v}</dd>
          </div>
        ))}
      </dl>

      {grips.length > 0 && (
        <section className="card">
          <h2 className="h2">Grip strength trend</h2>
          <GripTrend values={grips} cutoff={gripCutoff(p.sex)} />
        </section>
      )}

      <section className="card">
        <h2 className="h2">Visit history</h2>
        <ScreeningTable rows={visits} />
      </section>
    </>
  );
}
