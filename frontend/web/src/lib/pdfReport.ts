import jsPDF from "jspdf";
import { api } from "./api";
import { CHAIR_CUTOFF, SEX_LABEL, STAGE, TIER, finalStage, type Patient, type Screening, type Stage, type Tier } from "./store";

// The built-in PDF fonts only cover Latin-1, so every string here sticks to plain characters.

// Shown in the letterhead. Typed on the sign-in page and remembered on this device; the default makes
// it obvious when nothing was entered.
const saved = (key: string) => (typeof localStorage === "undefined" ? "" : (localStorage.getItem(key) ?? ""));

const DISCLAIMER =
  "SarcoScan is a screening and referral aid built as a hackathon prototype. It is not a medical device and does not replace a DEXA scan or a doctor's judgement.";

type Rgb = [number, number, number];
const INK: Rgb = [15, 23, 42];
const MUTED: Rgb = [100, 116, 139];
const LINE: Rgb = [226, 232, 240];
const BRAND: Rgb = [2, 132, 199];
const BRAND_DARK: Rgb = [3, 105, 161];
const GOOD: Rgb = [4, 120, 87];
const WARN: Rgb = [180, 83, 9];
const BAD: Rgb = [185, 28, 28];
/** The colour at the given strength over white: a see-through look without PDF transparency. */
const tint = (color: Rgb, strength: number) => color.map((c) => Math.round(255 - (255 - c) * strength)) as Rgb;
// The word is always printed next to the colour; the colour alone never carries the meaning.
const STAGE_INK: Record<Stage, Rgb> = { none: GOOD, possible: WARN, probable: [194, 65, 12], severe: BAD };
const TIER_INK: Record<Tier, Rgb> = { low: GOOD, moderate: WARN, high: BAD };

export type Picture = { data: string; width: number; height: number };

/** A picture as a data URL with its pixel size, or null if it cannot be loaded. */
async function picture(source: Promise<Blob>, type: "image/jpeg" | "image/png"): Promise<Picture | null> {
  try {
    const bitmap = await createImageBitmap(await source);
    const canvas = document.createElement("canvas");
    canvas.width = bitmap.width;
    canvas.height = bitmap.height;
    canvas.getContext("2d")!.drawImage(bitmap, 0, 0);
    return { data: canvas.toDataURL(type, 0.85), width: bitmap.width, height: bitmap.height };
  } catch {
    return null;
  }
}

/** Lay out the report from what the backend stored: page 1 the findings, page 2 the X-ray. */
export function buildReport(patient: Patient, s: Screening, logo: Picture | null, xray: Picture | null): jsPDF {
  const doc = new jsPDF({ unit: "mm", format: "a4" });
  const width = doc.internal.pageSize.getWidth();
  const height = doc.internal.pageSize.getHeight();
  const left = 14;
  const right = width - 14;
  const span = right - left;
  const reportNo = s.id.slice(0, 8).toUpperCase();
  const stage = finalStage(s);
  const HOSPITAL = saved("hospitalName") || "Demo Hospital";
  const HOSPITAL_ADDRESS = saved("hospitalAddress");
  let y = 0;

  const write = (
    text: string,
    x: number,
    at: number,
    size: number,
    color: Rgb = INK,
    style = "normal",
    align: "left" | "right" | "center" = "left",
    maxWidth?: number,
  ) => {
    doc.setFont("helvetica", style).setFontSize(size).setTextColor(...color);
    doc.text(text, x, at, { align, maxWidth });
  };
  const lineCount = (text: string, size: number, maxWidth: number) =>
    doc.setFont("helvetica", "normal").setFontSize(size).splitTextToSize(text, maxWidth).length;

  /** Hospital on the left, the software on the right. Drawn at the top of every page. */
  const letterhead = () => {
    write(HOSPITAL, left, HOSPITAL_ADDRESS ? 15 : 17.6, 14, INK, "bold");
    if (HOSPITAL_ADDRESS) write(HOSPITAL_ADDRESS, left, 20, 8.5, MUTED);

    // The logo sits at the right edge with the name to its left.
    const logoWidth = logo ? (12 * logo.width) / logo.height : 0;
    if (logo) doc.addImage(logo.data, "PNG", right - logoWidth, 10, logoWidth, 12);
    const nameEnd = right - (logo ? logoWidth + 3 : 0);
    write("SarcoScan", nameEnd, 15, 14, INK, "bold", "right");
    write("AI-assisted screening aid", nameEnd, 20, 8.5, MUTED, "normal", "right");
    doc.setFillColor(...BRAND).rect(left, 25, span, 0.7, "F");
  };
  const heading = (text: string) => {
    y += 9;
    write(text.toUpperCase(), left, y, 9.5, BRAND_DARK, "bold");
    y += 2;
    doc.setDrawColor(...LINE).line(left, y, right, y);
    y += 6;
  };

  // --- Page 1: findings ---
  letterhead();
  write("Sarcopenia and Osteoporosis Screening Report", left, 35, 14, INK, "bold");
  write(`Report no. ${reportNo}`, right, 32, 8.5, INK, "bold", "right");
  const generated = new Date().toLocaleString("en-GB", { dateStyle: "medium", timeStyle: "short" });
  write(`Generated ${generated}`, right, 36.5, 8, MUTED, "normal", "right");

  doc.setFillColor(248, 250, 252).setDrawColor(...LINE).roundedRect(left, 41, span, 31, 2, 2, "FD");
  const field = (label: string, value: string, x: number, at: number) => {
    write(label, x, at, 8, MUTED);
    doc.setFont("helvetica", "bold").setFontSize(9.5);
    write(doc.splitTextToSize(value, 54)[0], x + 29, at, 9.5, INK, "bold");
  };
  field("Patient", patient.name, left + 4, 48.5);
  field("Record no. (MRN)", patient.mrn, left + 4, 54.5);
  field("Age and sex", `${patient.age} years, ${SEX_LABEL[patient.sex]}`, left + 4, 60.5);
  field("Height and weight", `${patient.heightCm} cm, ${patient.weightKg} kg`, left + 4, 66.5);
  field("Screening date", s.date, left + 96, 48.5);
  field("Screened by", s.by, left + 96, 54.5);
  field("Reviewed by", s.finalized ? (s.reviewedBy ?? "Doctor") : "Pending doctor review", left + 96, 60.5);
  field("Body mass index", s.bmi.toFixed(1), left + 96, 66.5);
  y = 72;

  heading("Result");
  const cardWidth = (span - 6) / 2;
  const card = (x: number, label: string, value: string, color: Rgb, note: string) => {
    doc.setFillColor(...tint(color, 0.1)).setDrawColor(...tint(color, 0.35)).roundedRect(x, y, cardWidth, 27, 2, 2, "FD");
    write(label, x + 6, y + 6.5, 8, MUTED, "bold");
    write(value, x + 6, y + 14.5, 16, color, "bold");
    write(note, x + 6, y + 20, 8, MUTED, "normal", "left", cardWidth - 10);
  };
  card(
    left,
    "SARCOPENIA STAGE",
    STAGE[stage].label,
    STAGE_INK[stage],
    s.override
      ? `Set by ${s.override.by}. The system's stage was ${STAGE[s.stage].label}.`
      : s.lowMuscle === null
        ? "Basis: AWGS 2019 rules on handgrip and chair stand"
        : "Basis: AWGS 2019 rules, with the muscle-mass model",
  );
  card(
    left + cardWidth + 6,
    "OSTEOPOROSIS RISK",
    s.osteoTier ? TIER[s.osteoTier].label : "Not available",
    s.osteoTier ? TIER_INK[s.osteoTier] : MUTED,
    s.osteoProb === null
      ? "Needs the AI model"
      : `Image model. Probability of the osteoporosis class: ${Math.round(s.osteoProb * 100)}%`,
  );
  y += 27;
  if (s.klGrade !== null) {
    y += 6;
    write(`Knee osteoarthritis grade (Kellgren-Lawrence): ${s.klGrade} of 4. For information only.`, left, y, 9);
  }

  heading("Measured values");
  doc.setFillColor(241, 245, 249).rect(left, y - 2, span, 7, "F");
  const columns = [left + 2, left + 62, left + 96, right - 2];
  ["Measure", "Value", "Reference"].forEach((title, i) => write(title, columns[i], y + 2.8, 8, MUTED, "bold"));
  write("Status", columns[3], y + 2.8, 8, MUTED, "bold", "right");
  y += 5;
  const measure = (name: string, value: string, reference: string, low?: boolean) => {
    write(name, columns[0], y + 4.8, 9.5, INK, "bold");
    write(value, columns[1], y + 4.8, 9.5);
    write(reference, columns[2], y + 4.8, 8.5, MUTED);
    if (low !== undefined) write(low ? "Flagged" : "Normal", columns[3], y + 4.8, 9, low ? BAD : GOOD, "bold", "right");
    y += 7;
    doc.setDrawColor(...LINE).line(left, y, right, y);
  };
  if (s.bestGrip === null) measure("Best handgrip", "Not entered", "");
  else measure("Best handgrip", `${s.bestGrip} kg`, `Low when below ${s.gripCutoff} kg (AWGS 2019)`, s.bestGrip < s.gripCutoff);
  if (s.chairStand != null)
    measure("5-chair-stand time", `${s.chairStand} s`, `Slow at ${CHAIR_CUTOFF} s or more (AWGS 2019)`, s.chairStand >= CHAIR_CUTOFF);
  if (s.sarcF != null) measure("SARC-F score", `${s.sarcF}`, "Positive at 4 or more (AWGS 2019)", s.sarcF >= 4);
  if (s.calfCm != null) measure("Calf circumference", `${s.calfCm} cm`, "Not used in the stage rule");
  if (s.waistCm != null) measure("Waist", `${s.waistCm} cm`, "Input of the muscle-mass model");
  if (s.armCm != null) measure("Upper arm circumference", `${s.armCm} cm`, "Input of the muscle-mass model");
  if (s.lowMuscle !== null)
    measure(
      "Muscle mass (model)",
      s.lowMuscle ? "Likely low" : "Likely normal",
      s.lowMuscleProb === null ? "" : `Model probability ${Math.round(s.lowMuscleProb * 100)}%`,
      s.lowMuscle,
    );
  if (s.boneLoss !== null)
    measure(
      "Bone loss from history (model)",
      s.boneLoss ? "Likely" : "Unlikely",
      s.boneLossProb === null ? "" : `Model probability ${Math.round(s.boneLossProb * 100)}%`,
      s.boneLoss,
    );
  const ratio = (x: number | null) => (x === null ? "Not available" : x.toFixed(2));
  measure("Thigh soft tissue to bone", ratio(s.features.thigh), "Prototype measure, no cutoff");
  measure("Calf soft tissue to bone", ratio(s.features.calf), "Prototype measure, no cutoff");

  if (s.lowMuscle !== null) {
    y += 5;
    write(
      "The two model rows above come from body measurements and history, learned from a US health survey (adults 20 to 59 for muscle mass). They are not validated on Indian or older patients.",
      left,
      y,
      8,
      MUTED,
      "italic",
      "left",
      span,
    );
    y += 4;
  }

  if (!s.modelConnected) {
    y += 6;
    write(
      "The AI model was not connected when this screening ran. The stage comes from handgrip and chair-stand rules only. Osteoporosis risk and the X-ray measurements were not produced.",
      left,
      y,
      9,
      WARN,
      "italic",
      "left",
      span,
    );
    y += 6;
  }

  heading("Suggested action");
  const action = STAGE[stage].action;
  const actionHeight = 5 * lineCount(action, 9.5, span - 10) + 5;
  doc.setFillColor(...tint(BRAND, 0.08)).setDrawColor(...tint(BRAND, 0.3)).roundedRect(left, y - 2, span, actionHeight, 2, 2, "FD");
  write(action, left + 6, y + 4, 9.5, INK, "normal", "left", span - 10);
  y += actionHeight - 2;

  if (s.override) {
    heading("Doctor's note");
    const note = s.override.reason || "No note given.";
    write(note, left, y, 9.5, INK, "normal", "left", span);
    y += 5 * lineCount(note, 9.5, span);
  }

  // Names of who screened and who reviewed, anchored near the foot of the page.
  if (y > height - 48) {
    doc.addPage();
    letterhead();
  }
  const sign = height - 40;
  const signer = (x: number, name: string, role: string, pending = false) => {
    doc.setDrawColor(...MUTED).line(x, sign, x + 70, sign);
    write(name, x, sign + 5, 9.5, pending ? MUTED : INK, pending ? "italic" : "bold");
    write(role, x, sign + 9.5, 8, MUTED);
  };
  signer(left, s.by, "Screened by");
  signer(right - 70, s.finalized ? (s.reviewedBy ?? "Doctor") : "Pending doctor review", "Reviewing doctor", !s.finalized);

  // --- Page 2: the X-ray ---
  if (xray) {
    doc.addPage();
    letterhead();
    write("Knee X-ray", left, 35, 14, INK, "bold");
    write(`Report no. ${reportNo}`, right, 35, 8.5, INK, "bold", "right");
    write(`${patient.name} | Record no. ${patient.mrn} | Screened ${s.date}`, left, 41, 9, MUTED);
    const top = 47;
    const scale = Math.min(160 / xray.width, (height - 36 - top) / xray.height);
    const w = xray.width * scale;
    const h = xray.height * scale;
    const x = left + (span - w) / 2;
    doc.addImage(xray.data, "JPEG", x, top, w, h);
    doc.setDrawColor(...LINE).rect(x, top, w, h);
    write(
      `Knee AP X-ray as uploaded for this screening.${s.hasOverlay ? "" : " No measurement overlay was produced."}`,
      width / 2,
      top + h + 6,
      8.5,
      MUTED,
      "normal",
      "center",
    );
  }

  const pages = doc.getNumberOfPages();
  for (let page = 1; page <= pages; page++) {
    doc.setPage(page);
    doc.setDrawColor(...LINE).line(left, height - 20, right, height - 20);
    write(DISCLAIMER, left, height - 16, 7.5, MUTED, "normal", "left", span);
    write(`${HOSPITAL} | Report no. ${reportNo}`, left, height - 6, 7.5, MUTED);
    write(`Page ${page} of ${pages}`, right, height - 6, 7.5, MUTED, "normal", "right");
  }
  return doc;
}

/** Build the report and download it. */
export async function downloadReport(patient: Patient, s: Screening): Promise<void> {
  const [logo, xray] = await Promise.all([
    picture(
      fetch("/logo-mark.png").then((r) => r.blob()),
      "image/png",
    ),
    s.xrayId ? picture(api.blob(`/xrays/${s.xrayId}/image`), "image/jpeg") : null,
  ]);
  buildReport(patient, s, logo, xray).save(`SarcoScan_${patient.mrn}_${s.date}.pdf`);
}
