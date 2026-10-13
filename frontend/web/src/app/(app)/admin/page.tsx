"use client";

import { useState } from "react";
import { createStaff, setStaffActive, useStore, type Role } from "@/lib/store";

export default function Admin() {
  const { user, audit, staff } = useStore();
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");
  if (user?.role !== "admin") return <p>Admin access only.</p>;

  async function run(action: () => Promise<void>, done: string) {
    setBusy(true);
    setMessage("");
    try {
      await action();
      setMessage(done);
    } catch (err) {
      setMessage(err instanceof Error ? err.message : "Something went wrong. Try again.");
    } finally {
      setBusy(false);
    }
  }

  function add(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const form = e.currentTarget;
    const f = new FormData(form);
    const email = String(f.get("email")).trim();
    run(async () => {
      await createStaff({
        name: String(f.get("name")).trim(),
        email,
        role: f.get("role") as Role,
        password: String(f.get("password")),
      });
      form.reset();
    }, `Account created for ${email}.`);
  }

  return (
    <>
      <h1 className="h1">Admin</h1>

      <section className="card space-y-4">
        <h2 className="h2">Staff accounts</h2>
        <p className="text-sm text-[#64748b]">
          Doctors can also create their own account on the sign-in page. An admin account can only be made here.
        </p>
        <form onSubmit={add} className="grid gap-3 sm:grid-cols-2 lg:grid-cols-[1fr_1fr_auto_1fr_auto] lg:items-end">
          <label className="label">
            Full name
            <input name="name" required minLength={2} maxLength={120} autoComplete="off" className="input" />
          </label>
          <label className="label">
            Work email
            <input name="email" type="email" required autoComplete="off" className="input" />
          </label>
          <label className="label">
            Role
            <select name="role" required className="input">
              <option value="doctor">Doctor</option>
              <option value="admin">Admin</option>
            </select>
          </label>
          <label className="label">
            First password
            <input name="password" type="text" required maxLength={200} autoComplete="off" className="input" />
          </label>
          <button className="btn" disabled={busy}>
            Create account
          </button>
        </form>
        {message && (
          <p role="status" className="text-sm font-medium">
            {message}
          </p>
        )}
        <div className="overflow-x-auto">
          <table className="table">
            <thead>
              <tr>
                <th>Name</th>
                <th>Email</th>
                <th>Role</th>
                <th>Last sign-in</th>
                <th>Status</th>
                <th />
              </tr>
            </thead>
            <tbody>
              {staff.map((member) => (
                <tr key={member.id}>
                  <td>{member.name}</td>
                  <td>{member.email}</td>
                  <td className="capitalize">{member.role}</td>
                  <td className="whitespace-nowrap">
                    {member.last_login_at ? new Date(member.last_login_at).toLocaleString() : "Never"}
                  </td>
                  <td className={member.is_active ? "" : "font-semibold text-red-700"}>
                    {member.is_active ? "Active" : "Switched off"}
                  </td>
                  <td>
                    {member.email !== user.email && (
                      <button
                        className="btn-ghost px-2 py-1 text-xs"
                        disabled={busy}
                        onClick={() => run(() => setStaffActive(member.id, !member.is_active), "Saved.")}
                      >
                        {member.is_active ? "Switch off" : "Switch on"}
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

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
    </>
  );
}
