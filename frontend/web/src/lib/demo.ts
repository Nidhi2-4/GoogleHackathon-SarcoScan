// The demo doctor for the hackathon, public on purpose: made-up patients only. The login page lists
// it; the Admin page creates it in one click and can deactivate it. Remove before real use.
// No admin account here: a public admin could lock everyone else out.
export const DEMO_PASSWORD = "demo@123";

export const DEMO_ACCOUNTS = [
  { name: "Demo Doctor", role: "doctor", label: "Doctor", email: "demo1@doctor.com" },
] as const;
