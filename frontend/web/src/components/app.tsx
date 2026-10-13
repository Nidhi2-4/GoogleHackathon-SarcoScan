"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import {
  CHAIR_CUTOFF,
  STAGE,
  TIER,
  finalStage,
  useStore,
  type Patient,
  type Screening,
  type Stage,
  type Tier,
} from "@/lib/store";
import { DiagnosticHeatmap } from "./DiagnosticHeatmap";
import { FlameIcon, LayersIcon, ScanIcon } from "./Icons";

export const StageBadge = ({ stage }: { stage: Stage }) => (
  <span className={`badge ${STAGE[stage].cls}`}>{STAGE[stage].label}</span>
);

/** Osteoporosis risk comes only from the ML model, so it is empty until one is connected. */
export const TierBadge = ({ tier }: { tier: Tier | null }) =>
  tier ? <span className={`badge ${TIER[tier].cls}`}>{TIER[tier].label}</span> : <span className="text-[#64748b]">Not available</span>;

export const pct = (x: number) => `${Math.round(x * 100)}%`;
const kg = (x: number | null) => (x === null ? "Not entered" : `${x} kg`);
const ratio = (x: number | null) => (x === null ? "Not available" : x.toFixed(2));

/** Whether the backend has an ML model. Shown wherever a result depends on it. */
export function ModelStatus() {
  const { modelConnected, tabularConnected } = useStore();
  if (modelConnected === null) return null;
  // The hosted API has memory for the measurement models only (docs/DEPLOY.md), so say which part runs.
  const label = modelConnected ? "connected" : tabularConnected ? "measurements only, no X-ray model" : "not connected";
  return (
    <span className={`badge ${modelConnected ? "bg-emerald-100 text-emerald-800" : "bg-amber-100 text-amber-800"}`}>
      AI model: {label}
    </span>
  );
}

/** Screenings table shared by the dashboard, reports list and patient history. */
export function ScreeningTable({ rows }: { rows: Screening[] }) {
  const { patients } = useStore();
  if (!rows.length) return <p className="text-sm text-[#64748b]">No screenings yet.</p>;
  return (
    <div className="overflow-x-auto">
      <table className="table">
        <thead>
          <tr>
            <th>Date</th>
            <th>Patient</th>
            <th>Best grip</th>
            <th>Sarcopenia</th>
            <th>Osteoporosis risk</th>
            <th>Status</th>
            <th />
          </tr>
        </thead>
        <tbody>
          {rows.map((s) => {
            const p = patients.find((x) => x.id === s.patientId);
            return (
              <tr key={s.id}>
                <td>{s.date}</td>
                <td>{p ? <Link href={`/patients/${p.id}`}>{p.name}</Link> : "Unknown"}</td>
                <td>{kg(s.bestGrip)}</td>
                <td>
                  <StageBadge stage={finalStage(s)} />
                </td>
                <td>
                  <TierBadge tier={s.osteoTier} /> {s.osteoProb !== null && pct(s.osteoProb)}
                </td>
                <td>{s.finalized ? "Reviewed" : "Pending review"}</td>
                <td>
                  <Link href={`/reports/${s.id}`} className="font-semibold underline">
                    Report
                  </Link>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

export const byDateDesc = (a: Screening, b: Screening) => b.date.localeCompare(a.date) || b.id.localeCompare(a.id);

/** The uploaded X-ray, segmentation overlay, and Grad-CAM heatmap viewer. */
export function XrayImage({
  xrayId,
  hasOverlay,
  stage,
  riskScore,
  softTissueRatio,
  osteoRisk,
}: {
  xrayId: string;
  hasOverlay: boolean;
  stage?: string;
  riskScore?: number;
  softTissueRatio?: number;
  osteoRisk?: string;
}) {
  const [urls, setUrls] = useState<{ image?: string; overlay?: string; failed?: boolean }>({});
  const [viewMode, setViewMode] = useState<"heatmap" | "overlay" | "raw">("heatmap");

  useEffect(() => {
    let cancelled = false;
    const made: string[] = [];
    const load = (path: string) =>
      api.blob(path).then((blob) => {
        const url = URL.createObjectURL(blob);
        made.push(url);
        return url;
      });
    Promise.all([load(`/xrays/${xrayId}/image`), hasOverlay ? load(`/xrays/${xrayId}/overlay`) : undefined])
      .then(([image, overlay]) => !cancelled && setUrls({ image, overlay }))
      .catch(() => !cancelled && setUrls({ failed: true }));
    return () => {
      cancelled = true;
      made.forEach(URL.revokeObjectURL);
    };
  }, [xrayId, hasOverlay]);

  if (urls.failed) return <p className="text-sm text-red-700">The X-ray could not be loaded.</p>;
  if (!urls.image) return <p className="text-sm text-[#64748b]">Loading X-ray and AI heatmaps...</p>;

  return (
    <div className="space-y-4">
      {/* Mode Switcher Tabs */}
      <div className="no-print inline-flex p-1 rounded-xl bg-slate-100 border border-slate-200 text-xs font-semibold">
        <button
          type="button"
          onClick={() => setViewMode("heatmap")}
          className={`px-3 py-1.5 rounded-lg transition-all flex items-center gap-1.5 ${
            viewMode === "heatmap" ? "bg-white text-sky-700 shadow-sm font-bold" : "text-slate-600 hover:text-slate-900"
          }`}
        >
          <FlameIcon className="w-3.5 h-3.5 text-rose-500" />
          <span>AI Grad-CAM Heatmaps</span>
        </button>
        {urls.overlay && (
          <button
            type="button"
            onClick={() => setViewMode("overlay")}
            className={`px-3 py-1.5 rounded-lg transition-all flex items-center gap-1.5 ${
              viewMode === "overlay" ? "bg-white text-sky-700 shadow-sm font-bold" : "text-slate-600 hover:text-slate-900"
            }`}
          >
            <LayersIcon className="w-3.5 h-3.5 text-sky-600" />
            <span>UNet Segmentation Overlay</span>
          </button>
        )}
        <button
          type="button"
          onClick={() => setViewMode("raw")}
          className={`px-3 py-1.5 rounded-lg transition-all flex items-center gap-1.5 ${
            viewMode === "raw" ? "bg-white text-sky-700 shadow-sm font-bold" : "text-slate-600 hover:text-slate-900"
          }`}
        >
          <ScanIcon className="w-3.5 h-3.5 text-slate-500" />
          <span>Raw Knee Radiograph</span>
        </button>
      </div>

      {viewMode === "heatmap" ? (
        <DiagnosticHeatmap
          imageSrc={urls.image}
          stage={stage}
          riskScore={riskScore}
          softTissueRatio={softTissueRatio}
          osteoRisk={osteoRisk}
        />
      ) : (
        /* eslint-disable-next-line @next/next/no-img-element -- a blob fetched with the login token */
        <img
          src={viewMode === "overlay" && urls.overlay ? urls.overlay : urls.image}
          alt={viewMode === "overlay" ? "Knee X-ray with segmentation overlay" : "Uploaded knee X-ray"}
          className="max-h-96 rounded-lg bg-black object-contain"
        />
      )}
    </div>
  );
}

/** Result summary and measured-vs-cutoff table, shared by the wizard's last step and the report. */
export function Findings({ patient, r, stage = r.stage }: { patient: Patient; r: Screening; stage?: Stage }) {
  const calfCut = patient.sex === "M" ? 34 : 33;
  // [measurement, value, flag when, flagged?]. null in the last place means there is no cutoff to compare with.
  const rows: [string, string, string, boolean | null][] = [
    ["Best handgrip", kg(r.bestGrip), `< ${r.gripCutoff} kg`, r.bestGrip === null ? null : r.bestGrip < r.gripCutoff],
  ];
  if (r.chairStand != null) rows.push(["5-chair-stand time", `${r.chairStand} s`, `>= ${CHAIR_CUTOFF} s`, r.chairStand >= CHAIR_CUTOFF]);
  if (r.sarcF != null) rows.push(["SARC-F score", `${r.sarcF}`, ">= 4", r.sarcF >= 4]);
  if (r.calfCm != null) rows.push(["Calf circumference", `${r.calfCm} cm`, `< ${calfCut} cm`, r.calfCm < calfCut]);
  rows.push(
    ["Thigh soft-tissue to bone ratio", ratio(r.features.thigh), "prototype, no cutoff yet", null],
    ["Calf soft-tissue to bone ratio", ratio(r.features.calf), "prototype, no cutoff yet", null],
  );

  return (
    <>
      {!r.modelConnected && (
        <p role="status" className="card border-amber-300 bg-amber-50 text-sm">
          <strong>The AI model is not connected yet.</strong> The sarcopenia stage below comes from the AWGS 2019 rules on
          handgrip and chair-stand time. Osteoporosis risk, the overlay, and the X-ray measurements need the model and are
          shown as not available. Nothing on this page is estimated.
        </p>
      )}
      <dl className="grid gap-4 sm:grid-cols-3">
        <div className="card">
          <dt className="h2">Sarcopenia stage</dt>
          <dd>
            <StageBadge stage={stage} />
            <span className="mt-1 block text-xs text-[#64748b]">
              From AWGS 2019 rules on grip and chair stand
              {r.lowMuscle === null ? ". No muscle estimate was available." : ", plus the muscle-mass model below."}
            </span>
          </dd>
        </div>
        <div className="card">
          <dt className="h2">Osteoporosis risk</dt>
          <dd>
            <TierBadge tier={r.osteoTier} />
            {r.osteoProb !== null && <span className="text-sm"> model probability {pct(r.osteoProb)}</span>}
          </dd>
        </div>
        <div className="card">
          <dt className="h2">BMI</dt>
          <dd className="text-xl font-bold">{r.bmi.toFixed(1)}</dd>
        </div>
      </dl>
      <div className="overflow-x-auto">
        <table className="table">
          <thead>
            <tr>
              <th>Measurement</th>
              <th>Value</th>
              <th>Flag when</th>
              <th>Result</th>
            </tr>
          </thead>
          <tbody>
            {rows.map(([name, value, cut, low]) => (
              <tr key={name}>
                <td>{name}</td>
                <td>{value}</td>
                <td>{cut}</td>
                <td className={low ? "font-semibold text-red-700" : ""}>{low === null ? "" : low ? "Flagged" : "Normal"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {r.klGrade !== null && <p className="text-sm">Knee osteoarthritis grade (KL): {r.klGrade}. For information only.</p>}
      {r.lowMuscle !== null && (
        <div className="card text-sm">
          <h2 className="h2">From body measurements and history (second models)</h2>
          <p>
            Muscle mass: <strong>{r.lowMuscle ? "Likely low" : "Likely normal"}</strong>
            {r.lowMuscleProb !== null && ` (model probability ${pct(r.lowMuscleProb)})`}. Used in the sarcopenia stage.
          </p>
          {r.boneLoss !== null && (
            <p>
              Bone loss from history: <strong>{r.boneLoss ? "Likely" : "Unlikely"}</strong>
              {r.boneLossProb !== null && ` (model probability ${pct(r.boneLossProb)})`}. A second opinion next to the X-ray
              result; if the two disagree, the doctor decides.
            </p>
          )}
          <p className="mt-1 text-xs text-[#64748b]">
            These two models learned from a US health survey (adults 20 to 59 for muscle mass) and are not validated on
            Indian or older patients.
            {(r.waistCm == null || r.armCm == null) && " Waist or arm circumference was not entered, so the model used typical values."}
            {!r.historyAsked && " Medical history was not asked, so the model used typical answers."}
          </p>
        </div>
      )}
      <p className="text-sm">
        <strong>Suggested action:</strong> {STAGE[stage].action}
      </p>
      <p className="text-xs text-[#64748b]">Screening aid only, not a diagnosis. A DEXA scan is needed to confirm.</p>
    </>
  );
}
