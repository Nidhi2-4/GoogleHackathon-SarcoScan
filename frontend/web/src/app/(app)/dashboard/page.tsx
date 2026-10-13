"use client";

import Link from "next/link";
import { ScreeningTable, byDateDesc } from "@/components/app";
import { finalStage, useStore } from "@/lib/store";

export default function Dashboard() {
  const { user, patients, screenings } = useStore();
  const stats = [
    ["Patients", patients.length],
    ["Screenings", screenings.length],
    ["Pending review", screenings.filter((s) => !s.finalized).length],
    ["Probable or severe", screenings.filter((s) => ["probable", "severe"].includes(finalStage(s))).length],
  ];

  return (
    <>
      <header className="flex flex-wrap items-center justify-between gap-3">
        <h1 className="h1">Welcome, {user?.name}</h1>
        <Link href="/patients/new" className="btn">
          New patient
        </Link>
      </header>

      <dl className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        {stats.map(([label, value]) => (
          <div key={label} className="card">
            <dt className="text-xs font-semibold tracking-wider text-[#64748b] uppercase">{label}</dt>
            <dd className="mt-1 text-3xl font-bold">{value}</dd>
          </div>
        ))}
      </dl>

      <section className="card">
        <h2 className="h2">Recent screenings</h2>
        <ScreeningTable rows={[...screenings].sort(byDateDesc).slice(0, 8)} />
      </section>
    </>
  );
}
