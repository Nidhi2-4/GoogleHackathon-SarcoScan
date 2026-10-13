"use client";

import { useStore } from "@/lib/store";

export default function Admin() {
  const { user, audit } = useStore();
  if (user?.role !== "admin") return <p>Admin access only.</p>;

  return (
    <>
      <h1 className="h1">Admin</h1>

      <section className="card overflow-x-auto">
        <h2 className="h2">Audit log</h2>
        <p className="mb-3 text-sm text-[#64748b]">
          Every sign-in and every view or change of patient data. Rows can be added but not edited or deleted. Records
          are shown by id; patient names are never written here.
        </p>
        <table className="table">
          <thead>
            <tr>
              <th>Time</th>
              <th>User id</th>
              <th>Action</th>
              <th>Record</th>
              <th>IP address</th>
            </tr>
          </thead>
          <tbody>
            {audit.map((a, i) => (
              <tr key={i}>
                <td className="whitespace-nowrap">{new Date(a.at).toLocaleString()}</td>
                <td className="font-mono">{a.user}</td>
                <td className="font-semibold">{a.action}</td>
                <td className="font-mono">{a.record}</td>
                <td className="font-mono">{a.ip}</td>
              </tr>
            ))}
          </tbody>
        </table>
        {!audit.length && <p className="p-3 text-sm text-[#64748b]">No entries yet.</p>}
      </section>

      <section className="card">
        <h2 className="h2">Users</h2>
        <p className="text-sm text-[#64748b]">
          The first admin, doctor and technician are created on the server with <code>python -m backend.seed</code>.
          Managing users from this page is planned after the MVP.
        </p>
      </section>
    </>
  );
}
