"use client";

import Link from "next/link";
import { useState } from "react";
import { StageBadge, byDateDesc } from "@/components/app";
import { finalStage, useStore } from "@/lib/store";

export default function Patients() {
  const { user, patients, screenings } = useStore();
  const [q, setQ] = useState("");
  const rows = patients.filter((p) => `${p.name} ${p.mrn} ${p.phone ?? ""}`.toLowerCase().includes(q.toLowerCase()));

  return (
    <>
      <header className="flex flex-wrap items-center justify-between gap-3">
        <h1 className="h1">Patients</h1>
        {user?.role === "doctor" && (
          <Link href="/patients/new" className="btn">
            New patient
          </Link>
        )}
      </header>
      <input
        type="search"
        aria-label="Search patients"
        placeholder="Search by name, MRN or phone"
        className="input max-w-sm"
        value={q}
        onChange={(e) => setQ(e.target.value)}
      />
      <section className="card overflow-x-auto">
        <table className="table">
          <thead>
            <tr>
              <th>MRN</th>
              <th>Name</th>
              <th>Age / Sex</th>
              <th>Visits</th>
              <th>Latest stage</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((p) => {
              const visits = screenings.filter((s) => s.patientId === p.id).sort(byDateDesc);
              return (
                <tr key={p.id}>
                  <td>{p.mrn}</td>
                  <td>
                    <Link href={`/patients/${p.id}`} className="font-semibold underline">
                      {p.name}
                    </Link>
                  </td>
                  <td>
                    {p.age} / {p.sex}
                  </td>
                  <td>{visits.length}</td>
                  <td>{visits[0] ? <StageBadge stage={finalStage(visits[0])} /> : "Not screened"}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
        {!rows.length && <p className="p-3 text-sm text-[#64748b]">No patients match.</p>}
      </section>
    </>
  );
}
