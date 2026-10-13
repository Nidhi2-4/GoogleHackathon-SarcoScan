"use client";

import { useState } from "react";
import { ScreeningTable, byDateDesc } from "@/components/app";
import { useStore } from "@/lib/store";

export default function Reports() {
  const { screenings } = useStore();
  const [pending, setPending] = useState(false);

  return (
    <>
      <h1 className="h1">Reports</h1>
      <label className="flex items-center gap-2 text-sm">
        <input type="checkbox" checked={pending} onChange={(e) => setPending(e.target.checked)} />
        Pending review only
      </label>
      <section className="card">
        <ScreeningTable rows={screenings.filter((s) => !pending || !s.finalized).sort(byDateDesc)} />
      </section>
    </>
  );
}
