"use client";

import { ModelStatus } from "@/components/app";
import { useStore } from "@/lib/store";

export default function Settings() {
  const { user, modelConnected } = useStore();

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
