"use client";

import { useEffect, useState } from "react";
import { ModelStatus } from "@/components/app";
import { useStore } from "@/lib/store";

export default function Settings() {
  const { user, modelConnected } = useStore();
  // Printed on the PDF letterhead. A setting of this device, not patient data, so it lives in the browser.
  const [hospital, setHospital] = useState({ hospitalName: "", hospitalAddress: "" });
  const [saved, setSaved] = useState(false);
  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect -- read once from the browser after mount
    setHospital({
      hospitalName: localStorage.getItem("hospitalName") ?? "",
      hospitalAddress: localStorage.getItem("hospitalAddress") ?? "",
    });
  }, []);

  function saveHospital(e: React.FormEvent) {
    e.preventDefault();
    for (const [key, value] of Object.entries(hospital)) localStorage.setItem(key, value.trim());
    setSaved(true);
  }

  return (
    <>
      <h1 className="h1">Settings</h1>
      <dl className="card grid max-w-xl grid-cols-[6rem_1fr] gap-2 text-sm">
        <dt className="text-[#64748b]">Name</dt>
        <dd>{user?.name}</dd>
        <dt className="text-[#64748b]">Email</dt>
        <dd>{user?.email}</dd>
        <dt className="text-[#64748b]">Role</dt>
        <dd className="capitalize">{user?.role}</dd>
      </dl>
      <form onSubmit={saveHospital} className="card max-w-xl space-y-3">
        <h2 className="h2">Report letterhead</h2>
        <label className="label">
          Hospital name
          <input
            maxLength={60}
            className="input"
            value={hospital.hospitalName}
            onChange={(e) => (setSaved(false), setHospital({ ...hospital, hospitalName: e.target.value }))}
          />
        </label>
        <label className="label">
          Hospital address (optional)
          <input
            maxLength={80}
            className="input"
            value={hospital.hospitalAddress}
            onChange={(e) => (setSaved(false), setHospital({ ...hospital, hospitalAddress: e.target.value }))}
          />
        </label>
        <div className="flex items-center gap-3">
          <button className="btn">Save</button>
          {saved && (
            <span role="status" className="text-sm">
              Saved on this device. New PDF reports will use it.
            </span>
          )}
        </div>
      </form>
      <section className="card max-w-xl space-y-3">
        <h2 className="h2">System</h2>
        <ModelStatus />
        <p className="text-sm text-[#64748b]">
          {modelConnected
            ? "Screenings use the AI model for osteoporosis risk and the X-ray measurements."
            : "Screenings still run: the sarcopenia stage comes from handgrip and chair-stand rules. Osteoporosis risk and the X-ray measurements appear once the model file is added on the server."}
        </p>
        <p className="text-sm text-[#64748b]">
          Patient data is stored on the hospital server. Nothing about a patient is kept in this browser.
        </p>
      </section>
    </>
  );
}
