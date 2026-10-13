"use client";

import { useSyncExternalStore } from "react";
import { api, login, logout, refresh } from "./api";

export type Role = "admin" | "doctor" | "technician";
export type Sex = "M" | "F" | "O";
export type Stage = "none" | "possible" | "probable" | "severe";
export type Tier = "low" | "moderate" | "high";

export type User = { name: string; email: string; role: Role };
export type Patient = {
  id: string;
  mrn: string;
  name: string;
  age: number;
  sex: Sex;
  heightCm: number;
  weightKg: number;
  phone?: string;
};
export type ScreeningInput = {
  left: number[];
  right: number[];
  sarcF?: number;
  chairStand?: number;
  calfCm?: number;
  waistCm?: number;
  armCm?: number;
  /** Medical-history answers. Leave out when the patient was not asked. */
  history?: Record<string, boolean>;
};
/** One analysed visit. Image-based fields are null until an ML model is connected to the backend. */
export type Screening = {
  id: string;
  patientId: string;
  date: string;
  by: string;
  xrayId: string | null;
  hasOverlay: boolean;
  modelConnected: boolean;
  bmi: number;
  bestGrip: number | null;
  bestLeft: number | null;
  bestRight: number | null;
  gripCutoff: number;
  sarcF?: number;
  chairStand?: number;
  calfCm?: number;
  features: { thigh: number | null; calf: number | null; plateau: number | null; areaRatio: number | null };
  stage: Stage;
  osteoProb: number | null;
  osteoTier: Tier | null;
  klGrade: number | null;
  /** From the two body-measurement models; null when they are not installed on the server. */
  lowMuscle: boolean | null;
  lowMuscleProb: number | null;
  boneLoss: boolean | null;
  boneLossProb: number | null;
  waistCm?: number;
  armCm?: number;
  historyAsked: boolean;
  override?: { stage: Stage; reason: string; by: string };
  reviewedBy?: string;
  finalized: boolean;
};
export type Audit = { at: string; user: string; action: string; record: string; ip: string };
type State = {
  ready: boolean;
  user: User | null;
  patients: Patient[];
  screenings: Screening[];
  audit: Audit[];
  modelConnected: boolean | null;
};

export const STAGE: Record<Stage, { label: string; cls: string; action: string }> = {
  none: { label: "No sarcopenia", cls: "bg-emerald-100 text-emerald-800", action: "No referral needed. Re-screen in 12 months." },
  possible: {
    label: "Possible",
    cls: "bg-amber-100 text-amber-800",
    action: "Advise resistance exercise and protein intake. Re-screen in 6 months.",
  },
  probable: {
    label: "Probable",
    cls: "bg-orange-100 text-orange-800",
    action: "Refer for DEXA or BIA confirmation. Start physiotherapy and nutrition review.",
  },
  severe: {
    label: "Severe",
    cls: "bg-red-100 text-red-800",
    action: "Urgent referral for DEXA confirmation, falls-risk assessment and geriatric review.",
  },
};
export const TIER: Record<Tier, { label: string; cls: string }> = {
  low: { label: "Low", cls: "bg-emerald-100 text-emerald-800" },
  moderate: { label: "Moderate", cls: "bg-amber-100 text-amber-800" },
  high: { label: "High", cls: "bg-red-100 text-red-800" },
};

// AWGS 2019 cutoffs. The backend applies the same ones; these are for instant feedback while typing.
export const gripCutoff = (sex: Sex) => (sex === "M" ? 28 : 18);
export const CHAIR_CUTOFF = 12;
/** The yes or no questions of the bone-loss model. Keys match HISTORY_QUESTIONS in backend/analysis.py. */
export const HISTORY_QUESTIONS: [string, string][] = [
  ["prior_hip_fracture", "Hip fracture before"],
  ["prior_wrist_fracture", "Wrist fracture before"],
  ["prior_spine_fracture", "Spine fracture before"],
  ["parent_hip_fracture", "A parent had a hip fracture"],
  ["steroid_use", "Takes steroid tablets"],
  ["smoker_ever", "Has ever smoked"],
  ["smoker_current", "Smokes now"],
  ["diabetes", "Diabetes"],
  ["prediabetes", "Prediabetes"],
  ["hypertension", "High blood pressure"],
  ["high_cholesterol", "High cholesterol"],
  ["arthritis", "Arthritis"],
  ["gout", "Gout"],
  ["weak_kidneys", "Kidney disease"],
  ["liver_condition", "Liver disease"],
  ["cancer", "Cancer, now or before"],
  ["heart_failure", "Heart failure"],
  ["coronary_heart_disease", "Coronary heart disease"],
  ["heart_attack", "Heart attack before"],
  ["stroke", "Stroke before"],
  ["vigorous_recreation", "Does vigorous exercise or sport"],
  ["moderate_recreation", "Does moderate exercise (brisk walk, cycling)"],
];
export const SEX_LABEL: Record<Sex, string> = { M: "Male", F: "Female", O: "Other" };
export const bmi = (p: Patient) => p.weightKg / (p.heightCm / 100) ** 2;
export const finalStage = (s: Screening) => s.override?.stage ?? s.stage;

// --- shapes the backend returns (FastAPI shows them at /docs) ---
type ApiPatient = {
  id: string;
  mrn: string;
  name: string;
  age: number;
  sex: "male" | "female" | "other";
  height_cm: number;
  weight_kg: number;
  phone: string | null;
};
type ApiResult = {
  visit_id: string;
  patient_id: string;
  visit_date: string;
  status: string;
  performed_by_name: string | null;
  reviewed_by_name: string | null;
  bmi: number;
  grip: { best_left: number | null; best_right: number | null; best_kg: number | null; cutoff_kg: number };
  sarcf_score: number | null;
  chair_stand_5_sec: number | null;
  calf_circumference_cm: number | null;
  xray_id: string | null;
  has_overlay: boolean;
  model_connected: boolean;
  sarcopenia_stage: Stage | null;
  osteoporosis_prob: number | null;
  osteoporosis_tier: Tier | null;
  thigh_soft_to_bone: number | null;
  calf_soft_to_bone: number | null;
  soft_to_plateau: number | null;
  soft_area_ratio: number | null;
  kl_grade: number | null;
  waist_cm: number | null;
  arm_circ_cm: number | null;
  history: Record<string, boolean> | null;
  low_muscle: boolean | null;
  low_muscle_prob: number | null;
  bone_loss: boolean | null;
  bone_loss_prob: number | null;
  review: { final_stage: Stage; agrees_with_ai: boolean; notes: string | null } | null;
};
type ApiAudit = { user_id: string; action: string; entity_type: string; entity_id: string | null; ip_address: string; created_at: string };

const SEX_FROM_API = { male: "M", female: "F", other: "O" } as const;
const SEX_TO_API = { M: "male", F: "female", O: "other" } as const;

const toPatient = (p: ApiPatient): Patient => ({
  id: p.id,
  mrn: p.mrn,
  name: p.name,
  age: p.age,
  sex: SEX_FROM_API[p.sex],
  heightCm: p.height_cm,
  weightKg: p.weight_kg,
  phone: p.phone ?? undefined,
});

function toScreening(r: ApiResult): Screening {
  return {
    id: r.visit_id,
    patientId: r.patient_id,
    date: r.visit_date.slice(0, 10),
    by: r.performed_by_name ?? "Unknown",
    xrayId: r.xray_id,
    hasOverlay: r.has_overlay,
    modelConnected: r.model_connected,
    bmi: r.bmi,
    bestGrip: r.grip.best_kg,
    bestLeft: r.grip.best_left,
    bestRight: r.grip.best_right,
    gripCutoff: r.grip.cutoff_kg,
    sarcF: r.sarcf_score ?? undefined,
    chairStand: r.chair_stand_5_sec ?? undefined,
    calfCm: r.calf_circumference_cm ?? undefined,
    features: {
      thigh: r.thigh_soft_to_bone,
      calf: r.calf_soft_to_bone,
      plateau: r.soft_to_plateau,
      areaRatio: r.soft_area_ratio,
    },
    stage: r.sarcopenia_stage!,
    osteoProb: r.osteoporosis_prob,
    osteoTier: r.osteoporosis_tier,
    klGrade: r.kl_grade,
    // ?? null: a backend that has not been restarted since these fields were added leaves them out.
    lowMuscle: r.low_muscle ?? null,
    lowMuscleProb: r.low_muscle_prob ?? null,
    boneLoss: r.bone_loss ?? null,
    boneLossProb: r.bone_loss_prob ?? null,
    waistCm: r.waist_cm ?? undefined,
    armCm: r.arm_circ_cm ?? undefined,
    historyAsked: r.history != null,
    override:
      r.review && !r.review.agrees_with_ai
        ? { stage: r.review.final_stage, reason: r.review.notes ?? "", by: r.reviewed_by_name ?? "Doctor" }
        : undefined,
    reviewedBy: r.review ? (r.reviewed_by_name ?? "Doctor") : undefined,
    finalized: r.status === "reviewed" || r.status === "reported",
  };
}

// Everything shown comes from the backend and is kept in memory only. Nothing about a patient is
// written to browser storage.
const EMPTY: State = { ready: false, user: null, patients: [], screenings: [], audit: [], modelConnected: null };
let state: State = EMPTY;
let started = false;
const subs = new Set<() => void>();

function set(next: Partial<State>) {
  state = { ...state, ...next };
  subs.forEach((f) => f());
}

/** Fetch everything the pages show. Called after login and after every change. */
export async function reload(): Promise<void> {
  const user = await api.get<User>("/auth/me");
  const [patients, results, health, audit] = await Promise.all([
    api.get<ApiPatient[]>("/patients"),
    api.get<ApiResult[]>("/visits"),
    api.get<{ model_connected: boolean }>("/health"),
    user.role === "admin" ? api.get<ApiAudit[]>("/audit-logs") : Promise.resolve([]),
  ]);
  set({
    ready: true,
    user,
    patients: patients.map(toPatient),
    // A visit that was started but never analysed has no result to show yet.
    screenings: results.filter((r) => r.sarcopenia_stage !== null).map(toScreening),
    modelConnected: health.model_connected,
    audit: audit.map((a) => ({
      at: a.created_at,
      user: a.user_id.slice(0, 8),
      action: a.action,
      record: a.entity_id ? `${a.entity_type} ${a.entity_id.slice(0, 8)}` : a.entity_type,
      ip: a.ip_address,
    })),
  });
}

function start() {
  if (started || typeof window === "undefined") return;
  started = true;
  // After a page reload the token in memory is gone; the refresh cookie gets a new one.
  refresh()
    .then((ok) => (ok ? reload() : set({ ready: true })))
    .catch(() => set({ ready: true, user: null }));
}

export async function signIn(email: string, password: string): Promise<void> {
  await login(email, password);
  await reload();
}

export async function signOut(): Promise<void> {
  await logout();
  set({ ...EMPTY, ready: true });
}

export async function registerPatient(p: Omit<Patient, "id">): Promise<string> {
  const created = await api.post<ApiPatient>("/patients", {
    mrn: p.mrn,
    name: p.name,
    age: p.age,
    sex: SEX_TO_API[p.sex],
    height_cm: p.heightCm,
    weight_kg: p.weightKg,
    phone: p.phone ?? null,
    consent_given: true,
  });
  await reload();
  return created.id;
}

export const startVisit = (patientId: string) =>
  api.post<{ id: string }>(`/patients/${patientId}/visits`).then((v) => v.id);

export async function saveInputs(visitId: string, input: ScreeningInput): Promise<void> {
  await api.post(`/visits/${visitId}/clinical-inputs`, {
    sarcf_score: input.sarcF ?? null,
    chair_stand_5_sec: input.chairStand ?? null,
    calf_circumference_cm: input.calfCm ?? null,
    waist_cm: input.waistCm ?? null,
    arm_circ_cm: input.armCm ?? null,
    history: input.history ?? null,
  });
  await api.post(`/visits/${visitId}/grip`, { left: input.left, right: input.right });
}

/** Upload the X-ray. The backend runs the quality check and says why an image is refused. */
export const uploadXray = (visitId: string, file: File) =>
  api.upload<{ id: string; qc_passed: boolean; qc_reason: string | null }>(`/visits/${visitId}/xray`, file);

export async function runAnalysis(visitId: string): Promise<Screening> {
  const result = await api.post<ApiResult>(`/visits/${visitId}/analyze`);
  await reload();
  return toScreening(result);
}

/** Doctor's decision. Without `stage` the doctor agrees with the system's result. */
export async function reviewScreening(visitId: string, stage?: Stage, reason?: string): Promise<void> {
  await api.post(`/visits/${visitId}/review`, {
    agrees_with_ai: stage === undefined,
    final_stage: stage ?? null,
    notes: reason || null,
  });
  await reload();
}

export const useStore = () =>
  useSyncExternalStore(
    (f) => {
      subs.add(f);
      start();
      return () => subs.delete(f);
    },
    () => state,
    () => EMPTY,
  );
