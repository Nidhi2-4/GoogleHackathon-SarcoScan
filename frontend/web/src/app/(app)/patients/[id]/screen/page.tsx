"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useState } from "react";
import { Findings, XrayImage } from "@/components/app";
import { downloadReport } from "@/lib/pdfReport";
import { HISTORY_QUESTIONS, gripCutoff, runAnalysis, saveInputs, startVisit, uploadXray, useStore, type Screening } from "@/lib/store";

const STEPS = ["Clinical inputs", "Handgrip", "X-ray upload", "Results"];
const HANDS = ["right", "left"] as const;
const num = (s: string) => (s === "" ? undefined : Number(s));
// SARC-F (Malmstrom and Morley): five questions, each scored 0, 1 or 2. The total is the score.
const SARC_F: [string, [string, string, string]][] = [
  ["Lifting and carrying about 4.5 kg", ["No difficulty", "Some", "A lot, or unable"]],
  ["Walking across a room", ["No difficulty", "Some", "A lot, uses aids, or unable"]],
  ["Getting up from a chair or bed", ["No difficulty", "Some", "A lot, or unable without help"]],
  ["Climbing 10 stairs", ["No difficulty", "Some", "A lot, or unable"]],
  ["Falls in the past year", ["None", "1 to 3 falls", "4 or more falls"]],
];

export default function ScreeningWizard() {
  const { id } = useParams<{ id: string }>();
  const { patients, user } = useStore();
  const patient = patients.find((p) => p.id === id);

  const [step, setStep] = useState(0);
  const [clin, setClin] = useState({ chairStand: "", calfCm: "", waistCm: "", armCm: "" });
  // One answer per SARC-F question; "" until it is asked. The score exists only when all five are answered.
  const [sarc, setSarc] = useState(["", "", "", "", ""]);
  const sarcScore = sarc.every((a) => a !== "") ? sarc.reduce((sum, a) => sum + Number(a), 0) : undefined;
  // null until the technician says the history was asked; then every unticked box means no.
  const [history, setHistory] = useState<Record<string, boolean> | null>(null);
  const [grip, setGrip] = useState({ right: ["", "", ""], left: ["", "", ""] });
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState("");
  const [visitId, setVisitId] = useState("");
  // What the server is doing right now, an error to show, or the finished result.
  const [progress, setProgress] = useState("");
  const [problem, setProblem] = useState("");
  const [result, setResult] = useState<Screening | null>(null);

  if (!patient) return <p>Patient not found.</p>;
  if (user?.role === "admin") return <p>Screenings are run by technicians and doctors.</p>;

  const next = (e: React.FormEvent) => {
    e.preventDefault();
    setStep(step + 1);
  };
  const best = Math.max(0, ...[...grip.right, ...grip.left].map(Number));
  const cutoff = gripCutoff(patient.sex);

  function pick(e: React.ChangeEvent<HTMLInputElement>) {
    const picked = e.target.files?.[0] ?? null;
    setFile(picked);
    setProblem("");
    setPreview(picked ? URL.createObjectURL(picked) : "");
  }

  /** Demo helper: made-up inputs and the sample image from public/samples, ready to run. */
  async function fillSample() {
    setClin({ chairStand: "13.5", calfCm: "31", waistCm: "78", armCm: "24" });
    setSarc(["1", "1", "1", "1", "1"]);
    setHistory({ prior_wrist_fracture: true, arthritis: true, hypertension: true });
    setGrip({ right: ["15.5", "16.2", "15.8"], left: ["14.1", "14.9", "14.4"] });
    const blob = await (await fetch("/samples/sample_knee_left.jpg")).blob();
    setFile(new File([blob], "sample_knee_left.jpg", { type: "image/jpeg" }));
    setPreview(URL.createObjectURL(blob));
    setProblem("");
    setStep(2);
  }

  /** The one explicit action: save the inputs, upload and check the X-ray, then run the analysis. */
  async function run(e: React.FormEvent) {
    e.preventDefault();
    if (!file) return;
    setProblem("");
    try {
      setProgress("Saving handgrip and clinical inputs");
      const visit = visitId || (await startVisit(patient!.id));
      setVisitId(visit);
      await saveInputs(visit, {
        right: grip.right.map(Number),
        left: grip.left.map(Number),
        sarcF: sarcScore,
        chairStand: num(clin.chairStand),
        calfCm: num(clin.calfCm),
        waistCm: num(clin.waistCm),
        armCm: num(clin.armCm),
        history: history ?? undefined,
      });
      setProgress("Uploading the X-ray and checking its quality");
      const xray = await uploadXray(visit, file);
      if (!xray.qc_passed) {
        setProblem(`This image cannot be used. ${xray.qc_reason ?? ""} Choose another image.`);
        return;
      }
      setProgress("Running the analysis");
      setResult(await runAnalysis(visit));
      setStep(3);
    } catch (err) {
      setProblem(err instanceof Error ? err.message : "Something went wrong. Try again.");
    } finally {
      setProgress("");
    }
  }

  return (
    <>
      <h1 className="h1">
        Screening <small className="text-sm font-normal text-[#64748b]">{patient.name}</small>
      </h1>
      <ol className="flex flex-wrap gap-2 text-xs font-semibold">
        {STEPS.map((s, i) => (
          <li
            key={s}
            aria-current={i === step ? "step" : undefined}
            className="rounded-full bg-white px-3 py-1 text-[#64748b] aria-[current]:bg-[#0284c7] aria-[current]:text-white"
          >
            {i + 1}. {s}
          </li>
        ))}
      </ol>
      {step < 3 && (
        <button type="button" className="btn-ghost" disabled={!!progress} onClick={fillSample}>
          Fill sample values
        </button>
      )}

      {step === 0 && (
        <form onSubmit={next} className="card grid max-w-2xl gap-4 sm:grid-cols-3">
          <p className="text-sm text-[#64748b] sm:col-span-3">All are optional. Leave blank if not measured.</p>
          <fieldset className="sm:col-span-3">
            <legend className="label mb-1">
              SARC-F questions. Score: <strong>{sarcScore ?? "-"}</strong> of 10
              {sarcScore !== undefined && (sarcScore >= 4 ? " (positive: 4 or more)" : " (negative)")}
            </legend>
            <div className="grid gap-3 sm:grid-cols-2">
              {SARC_F.map(([question, answers], i) => (
                <label key={question} className="label">
                  {question}
                  <select
                    className="input"
                    value={sarc[i]}
                    // All five or none: a half-answered questionnaire has no score.
                    required={sarc.some((a) => a !== "")}
                    onChange={(e) => setSarc(sarc.with(i, e.target.value))}
                  >
                    <option value="">Not asked</option>
                    {answers.map((answer, points) => (
                      <option key={answer} value={points}>
                        {answer} ({points})
                      </option>
                    ))}
                  </select>
                </label>
              ))}
            </div>
          </fieldset>
          <label className="label">
            5-chair-stand time (s)
            <input type="number" min={1} max={120} step="0.1" className="input" value={clin.chairStand} onChange={(e) => setClin({ ...clin, chairStand: e.target.value })} />
          </label>
          <label className="label">
            Calf circumference (cm)
            <input type="number" min={15} max={70} step="0.1" className="input" value={clin.calfCm} onChange={(e) => setClin({ ...clin, calfCm: e.target.value })} />
          </label>
          <label className="label">
            Waist (cm)
            <input type="number" min={41} max={199} step="0.1" className="input" value={clin.waistCm} onChange={(e) => setClin({ ...clin, waistCm: e.target.value })} />
          </label>
          <label className="label">
            Upper arm circumference (cm)
            <input type="number" min={11} max={69} step="0.1" className="input" value={clin.armCm} onChange={(e) => setClin({ ...clin, armCm: e.target.value })} />
          </label>
          <fieldset className="sm:col-span-3">
            <label className="flex items-center gap-2 text-sm font-medium">
              <input type="checkbox" checked={history !== null} onChange={(e) => setHistory(e.target.checked ? {} : null)} />
              Medical history was asked
            </label>
            {history !== null && (
              <div className="mt-2 grid gap-x-4 gap-y-2 text-sm sm:grid-cols-2">
                <p className="text-xs text-[#64748b] sm:col-span-2">Tick what applies. An unticked box is recorded as no.</p>
                {HISTORY_QUESTIONS.map(([key, label]) => (
                  <label key={key} className="flex min-h-11 items-center gap-2 sm:min-h-0">
                    <input type="checkbox" checked={!!history[key]} onChange={(e) => setHistory({ ...history, [key]: e.target.checked })} />
                    {label}
                  </label>
                ))}
              </div>
            )}
          </fieldset>
          <button className="btn sm:col-span-3 sm:justify-self-end">Next</button>
        </form>
      )}

      {step === 1 && (
        <form onSubmit={next} className="card max-w-2xl space-y-4">
          <p className="text-sm text-[#64748b]">Three trials per hand, in kg. The best value is used.</p>
          {HANDS.map((hand) => (
            <fieldset key={hand} className="grid grid-cols-3 gap-3">
              <legend className="label mb-1 capitalize">{hand} hand</legend>
              {grip[hand].map((v, i) => (
                <input
                  key={i}
                  type="number"
                  required
                  min={1}
                  max={99}
                  step="0.1"
                  aria-label={`${hand} hand trial ${i + 1}`}
                  placeholder={`Trial ${i + 1}`}
                  className="input"
                  value={v}
                  onChange={(e) => setGrip({ ...grip, [hand]: grip[hand].with(i, e.target.value) })}
                />
              ))}
            </fieldset>
          ))}
          <p className="text-sm">
            Best: <strong>{best || "-"} kg</strong>. AWGS 2019 cutoff for this patient: {cutoff} kg.
            {best > 0 && <strong className={best < cutoff ? "text-red-700" : "text-emerald-700"}> {best < cutoff ? "Low grip strength" : "Normal"}</strong>}
          </p>
          <div className="flex justify-between">
            <button type="button" className="btn-ghost" onClick={() => setStep(0)}>
              Back
            </button>
            <button className="btn">Next</button>
          </div>
        </form>
      )}

      {step === 2 && (
        <form onSubmit={run} className="card max-w-2xl space-y-4">
          <label className="label">
            Knee AP X-ray (JPG or PNG, up to 50 MB)
            <input type="file" required={!file} accept=".jpg,.jpeg,.png,image/jpeg,image/png" className="input" onChange={pick} />
          </label>
          {/* eslint-disable-next-line @next/next/no-img-element -- local preview of the chosen file */}
          {preview && <img src={preview} alt="Chosen knee X-ray" className="max-h-72 rounded-lg bg-black" />}
          {progress && (
            <p role="status" className="text-sm font-medium">
              {progress}...
            </p>
          )}
          {problem && (
            <p role="alert" className="text-sm font-medium text-red-700">
              {problem}
            </p>
          )}
          <div className="flex justify-between">
            <button type="button" className="btn-ghost" disabled={!!progress} onClick={() => setStep(1)}>
              Back
            </button>
            <button className="btn" disabled={!file || !!progress}>
              Run screening
            </button>
          </div>
        </form>
      )}

      {step === 3 && result && (
        <section className="space-y-4">
          <Findings patient={patient} r={result} />
          {result.xrayId && (
            <div className="card">
              <h2 className="h2">Knee X-ray</h2>
              <XrayImage xrayId={result.xrayId} hasOverlay={result.hasOverlay} />
            </div>
          )}
          <div className="flex flex-wrap justify-end gap-3">
            <button className="btn-ghost" onClick={() => downloadReport(patient, result)}>
              Download PDF report
            </button>
            <Link href={`/reports/${result.id}`} className="btn">
              Open report for review
            </Link>
          </div>
        </section>
      )}
    </>
  );
}
