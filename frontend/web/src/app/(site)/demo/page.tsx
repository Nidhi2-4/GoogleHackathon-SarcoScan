"use client";

import React, { useState, useRef, useId } from "react";
import Link from "next/link";
import {
  ActivityIcon,
  BoneIcon,
  ScanIcon,
  ShieldCheckIcon,
  SparklesIcon,
  PhoneIcon,
  MailIcon,
  CheckCircleIcon,
  AlertTriangleIcon,
  ArrowRightIcon,
  RefreshCwIcon,
  ServerIcon,
  UsersIcon,
  FileTextIcon,
  InfoIcon,
} from "@/components/Icons";
import { Skeleton, PatientReportSkeleton } from "@/components/ui/Skeleton";

// Preset Sample Knee AP X-Rays for quick testing
const CLINICAL_PRESETS = [
  {
    id: "case-normal",
    title: "Preset 1 · Preserved Muscle",
    patientName: "Patient A (Control)",
    age: 62,
    sex: "Male",
    height: 175,
    weight: 74,
    leftTrials: [33.0, 34.5, 34.0],
    rightTrials: [35.0, 36.2, 35.8],
    gripStrength: 36.2,
    bmi: 24.2,
    xrayType: "Normal Cortical & Trabecular Architecture",
    description: "Intact cortical bone thickness, normal proximal tibia trabecular density, thigh muscle ratio 2.14.",
    sarcopeniaStage: "No Sarcopenia",
    sarcopeniaColor: "text-emerald-700 bg-emerald-50 border-emerald-200",
    sarcopeniaProb: 12,
    osteoRisk: "Low Risk",
    osteoColor: "text-emerald-700 bg-emerald-50 border-emerald-200",
    osteoProb: 18,
    softTissueRatio: 2.14,
    altText: "Diagnostic knee radiograph showing intact cortical bone thickness and normal thigh muscle-to-bone ratio.",
  },
  {
    id: "case-mild",
    title: "Preset 2 · Borderline Muscle Loss",
    patientName: "Patient B (Possible Sarcopenia)",
    age: 71,
    sex: "Female",
    height: 160,
    weight: 56,
    leftTrials: [16.5, 17.0, 16.8],
    rightTrials: [17.5, 17.8, 17.2],
    gripStrength: 17.8,
    bmi: 21.8,
    xrayType: "Borderline Soft-Tissue Ratio",
    description: "Thigh soft tissue thinning, grip borderline below female cutoff (<18kg), slight trabecular reduction.",
    sarcopeniaStage: "Possible Sarcopenia",
    sarcopeniaColor: "text-amber-700 bg-amber-50 border-amber-200",
    sarcopeniaProb: 54,
    osteoRisk: "Moderate Risk",
    osteoColor: "text-amber-700 bg-amber-50 border-amber-200",
    osteoProb: 52,
    softTissueRatio: 1.58,
    altText: "Knee radiograph exhibiting borderline soft tissue thinning in the thigh compartment with mild trabecular reduction.",
  },
  {
    id: "case-severe",
    title: "Preset 3 · Severe Sarcopenia & Osteopenia",
    patientName: "Patient C (High Risk)",
    age: 79,
    sex: "Female",
    height: 154,
    weight: 45,
    leftTrials: [12.5, 13.0, 12.8],
    rightTrials: [13.2, 13.8, 13.5],
    gripStrength: 13.8,
    bmi: 19.0,
    xrayType: "Marked Muscle Atrophy & Trabecular Thinning",
    description: "Marked quadriceps muscle wasting, low proximal tibia cortical index, severe grip deficiency (<15kg).",
    sarcopeniaStage: "Severe Sarcopenia",
    sarcopeniaColor: "text-rose-700 bg-rose-50 border-rose-200",
    sarcopeniaProb: 89,
    osteoRisk: "High Risk",
    osteoColor: "text-rose-700 bg-rose-50 border-rose-200",
    osteoProb: 84,
    softTissueRatio: 1.12,
    altText: "Knee radiograph revealing severe soft-tissue muscle atrophy and pronounced proximal tibia bone mineral loss.",
  },
];

export default function DemoPage() {
  const fileInputId = useId();
  // Ingestion Mode: "upload" or "preset"
  const [ingestionMode, setIngestionMode] = useState<"upload" | "preset">("preset");
  const [selectedPreset, setSelectedPreset] = useState(CLINICAL_PRESETS[1]);

  // Uploaded Image State
  const [uploadedImage, setUploadedImage] = useState<string | null>(null);
  const [uploadedFileName, setUploadedFileName] = useState<string>("");
  const [showSegmentationMask, setShowSegmentationMask] = useState<boolean>(true);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Grip Input Mode: "detailed" (3 trials per hand) or "direct" (single value)
  const [gripInputMode, setGripInputMode] = useState<"detailed" | "direct">("detailed");

  // Patient Biomarkers
  const [patientName, setPatientName] = useState("Jane Doe");
  const [age, setAge] = useState<number>(71);
  const [sex, setSex] = useState<string>("Female");
  const [height, setHeight] = useState<number>(160);
  const [weight, setWeight] = useState<number>(56);

  // Manual 3-Trial Grip Data (kg)
  const [leftTrials, setLeftTrials] = useState<[number, number, number]>([16.5, 17.0, 16.8]);
  const [rightTrials, setRightTrials] = useState<[number, number, number]>([17.5, 17.8, 17.2]);
  const [directGrip, setDirectGrip] = useState<number>(17.8);

  // Optional Clinical Modifiers
  const [softTissueRatio, setSoftTissueRatio] = useState<number>(1.58);
  const [sarcFScore, setSarcFScore] = useState<number>(3);
  const [chairStandSec, setChairStandSec] = useState<number>(14.5);

  // Simulation states
  const [isLoading, setIsLoading] = useState(false);
  const [doctorOverride, setDoctorOverride] = useState(false);
  const [overrideStage, setOverrideStage] = useState("Probable Sarcopenia");
  const [doctorNotes, setDoctorNotes] = useState("");
  const [showExportSuccess, setShowExportSuccess] = useState(false);

  // Dynamic Peak Grip Calculation
  const peakCalculatedGrip =
    gripInputMode === "detailed"
      ? Math.max(...leftTrials, ...rightTrials)
      : directGrip;

  // Dynamic BMI Calculation
  const calculatedBMI = Number((weight / Math.pow(height / 100, 2)).toFixed(1));

  // AWGS 2019 Cutoff Rules: Male < 28 kg, Female < 18 kg
  const gripCutoff = sex === "Male" ? 28.0 : 18.0;
  const isGripDeficient = peakCalculatedGrip < gripCutoff;
  const gripDeficitMargin = (gripCutoff - peakCalculatedGrip).toFixed(1);

  // Multimodal AI Fusion Model Staging Algorithm
  let computedSarcopeniaStage = "No Sarcopenia";
  let computedSarcopeniaScore = 14;
  let sarcopeniaColor = "text-emerald-700 bg-emerald-50 border-emerald-200";

  if (peakCalculatedGrip < gripCutoff - 4 || (isGripDeficient && softTissueRatio < 1.35) || (isGripDeficient && calculatedBMI < 19.5)) {
    computedSarcopeniaStage = "Severe Sarcopenia";
    computedSarcopeniaScore = 88;
    sarcopeniaColor = "text-rose-700 bg-rose-50 border-rose-200";
  } else if (isGripDeficient && (softTissueRatio < 1.70 || sarcFScore >= 4 || chairStandSec > 12)) {
    computedSarcopeniaStage = "Probable Sarcopenia";
    computedSarcopeniaScore = 68;
    sarcopeniaColor = "text-amber-700 bg-amber-50 border-amber-200";
  } else if (isGripDeficient || (softTissueRatio < 1.65 && age >= 65)) {
    computedSarcopeniaStage = "Possible Sarcopenia";
    computedSarcopeniaScore = 46;
    sarcopeniaColor = "text-sky-800 bg-sky-50 border-sky-200";
  }

  // Proximal Tibia Osteoporosis Risk calculation
  let computedOsteoRisk = "Low Risk";
  let computedOsteoProb = 20;
  let osteoColor = "text-emerald-700 bg-emerald-50 border-emerald-200";

  if (age > 75 && (calculatedBMI < 20 || softTissueRatio < 1.35)) {
    computedOsteoRisk = "High Risk";
    computedOsteoProb = 85;
    osteoColor = "text-rose-700 bg-rose-50 border-rose-200";
  } else if (age >= 68 || calculatedBMI < 22 || softTissueRatio < 1.65) {
    computedOsteoRisk = "Moderate Risk";
    computedOsteoProb = 54;
    osteoColor = "text-amber-700 bg-amber-50 border-amber-200";
  }

  // Handle Preset Selection
  const handleSelectPreset = (preset: typeof CLINICAL_PRESETS[0]) => {
    setSelectedPreset(preset);
    setIngestionMode("preset");
    setPatientName(preset.patientName);
    setAge(preset.age);
    setSex(preset.sex);
    setHeight(preset.height);
    setWeight(preset.weight);
    setLeftTrials(preset.leftTrials as [number, number, number]);
    setRightTrials(preset.rightTrials as [number, number, number]);
    setDirectGrip(preset.gripStrength);
    setSoftTissueRatio(preset.softTissueRatio);
    setDoctorOverride(false);
    setDoctorNotes("");
    triggerFastInference();
  };

  // Handle File Upload
  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      const url = URL.createObjectURL(file);
      setUploadedImage(url);
      setUploadedFileName(file.name);
      setIngestionMode("upload");
      setSoftTissueRatio(1.62);
      triggerFastInference();
    }
  };

  const triggerFastInference = () => {
    setIsLoading(true);
    setTimeout(() => {
      setIsLoading(false);
    }, 350);
  };

  const handleUpdateTrial = (hand: "left" | "right", index: number, value: number) => {
    if (hand === "left") {
      const updated = [...leftTrials] as [number, number, number];
      updated[index] = value;
      setLeftTrials(updated);
    } else {
      const updated = [...rightTrials] as [number, number, number];
      updated[index] = value;
      setRightTrials(updated);
    }
  };

  return (
    <div className="bg-slate-50/50 py-10 px-4 sm:px-8">
      <div className="max-w-7xl mx-auto space-y-10">
        
        {/* Breadcrumb & Header */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 text-xs font-semibold text-sky-700 mb-1">
              <Link href="/" className="hover:underline">Home</Link>
              <span>/</span>
              <span className="text-slate-500">Interactive Clinical Demo</span>
            </div>
            <h1 className="text-3xl sm:text-4xl font-extrabold text-slate-900 tracking-tight">
              Knee X-Ray Ingestion &amp; Handgrip Strength Calculator
            </h1>
            <p className="text-sm text-slate-600 mt-1 max-w-3xl">
              Simulate on-premise AI inference by uploading a custom knee AP radiograph or choosing clinical presets, entering manual dynamometer readings, and calculating instant sarcopenia and osteoporosis risk stratifications.
            </p>
          </div>

          <div className="flex items-center gap-3">
            <button
              type="button"
              onClick={triggerFastInference}
              className="px-4 py-2.5 rounded-xl bg-sky-600 hover:bg-sky-700 text-white font-bold text-xs transition-all shadow-md shadow-sky-600/20 flex items-center gap-2"
            >
              <RefreshCwIcon className="w-4 h-4" />
              <span>Re-Run AI Inference</span>
            </button>
            <Link
              href="/login"
              className="px-4 py-2.5 rounded-xl bg-white border border-slate-200 text-slate-700 hover:bg-slate-50 font-semibold text-xs transition-all"
            >
              Clinical Portal &rarr;
            </Link>
          </div>
        </div>

        {/* 2. INTERACTIVE SCREENING STATION (BLUE & WHITE THEMED) */}
        <div className="p-6 sm:p-10 rounded-3xl bg-white border border-slate-200 shadow-xl shadow-sky-900/5 space-y-8">
          
          {/* STEP 1: KNEE X-RAY INGESTION MODE (UPLOAD OR PRESETS) */}
          <div className="space-y-4">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <span className="text-xs font-bold uppercase tracking-wider text-slate-900 flex items-center gap-2">
                <BoneIcon className="w-4 h-4 text-sky-600" />
                Step 1: Knee AP Radiograph Ingestion
              </span>

              {/* Mode Toggle Tabs */}
              <div className="inline-flex p-1 rounded-xl bg-slate-100 border border-slate-200 text-xs font-bold">
                <button
                  type="button"
                  onClick={() => setIngestionMode("upload")}
                  className={`px-3.5 py-1.5 rounded-lg transition-all ${
                    ingestionMode === "upload"
                      ? "bg-white text-sky-700 shadow-sm"
                      : "text-slate-600 hover:text-slate-900"
                  }`}
                >
                  Upload Your Own X-Ray
                </button>
                <button
                  type="button"
                  onClick={() => setIngestionMode("preset")}
                  className={`px-3.5 py-1.5 rounded-lg transition-all ${
                    ingestionMode === "preset"
                      ? "bg-white text-sky-700 shadow-sm"
                      : "text-slate-600 hover:text-slate-900"
                  }`}
                >
                  Choose Clinical Preset
                </button>
              </div>
            </div>

            {ingestionMode === "upload" ? (
              /* Custom File Upload Drag & Drop Area */
              <div className="grid grid-cols-1 md:grid-cols-12 gap-6 p-6 rounded-2xl bg-sky-50/40 border-2 border-dashed border-sky-300">
                <div className="md:col-span-6 space-y-4">
                  <label htmlFor={fileInputId} className="block text-xs font-bold text-slate-900">Upload Knee AP Radiograph (.PNG, .JPG, .DCM)</label>
                  <p className="text-xs text-slate-600">
                    Select or drag standard knee radiograph from your local device or PACS workstation. DICOM metadata tags will be de-identified on-premise.
                  </p>
                  <div className="flex items-center gap-3">
                    <input
                      id={fileInputId}
                      ref={fileInputRef}
                      type="file"
                      accept="image/*"
                      onChange={handleFileUpload}
                      className="hidden"
                    />
                    <button
                      type="button"
                      onClick={() => fileInputRef.current?.click()}
                      className="px-4 py-2.5 rounded-xl bg-sky-600 hover:bg-sky-700 text-white font-bold text-xs transition-all flex items-center gap-2 shadow-sm"
                    >
                      <ScanIcon className="w-4 h-4" />
                      <span>{uploadedFileName ? "Change Image" : "Browse & Upload X-Ray"}</span>
                    </button>
                    {uploadedFileName && (
                      <span className="text-xs font-semibold text-slate-700 truncate max-w-[200px]">
                        {uploadedFileName}
                      </span>
                    )}
                  </div>
                  <div className="p-3 rounded-xl bg-white border border-sky-100 text-xs text-slate-600 space-y-1">
                    <p className="font-semibold text-slate-800">Automatic QC Check</p>
                    <p className="flex items-center gap-1.5 text-emerald-700">
                      <CheckCircleIcon className="w-3.5 h-3.5" />
                      <span>Knee AP View Validated · No edge cropping detected</span>
                    </p>
                    <p className="text-slate-500">
                      • Thigh soft-tissue to cortical bone ratio estimated: <strong>{softTissueRatio}</strong>
                    </p>
                  </div>
                </div>

                <div className="md:col-span-6 flex flex-col items-center justify-center p-4 bg-white rounded-xl border border-slate-200 min-h-[220px]">
                  {uploadedImage ? (
                    <div className="relative w-full max-w-[260px] aspect-square rounded-lg overflow-hidden border border-slate-200 bg-black">
                      <img
                        src={uploadedImage}
                        alt="Uploaded Knee AP Radiograph"
                        className="w-full h-full object-contain"
                      />
                      {showSegmentationMask && (
                        <div className="absolute inset-0 bg-sky-500/20 border-2 border-sky-400 pointer-events-none flex items-end p-2">
                          <span className="text-[10px] font-bold bg-sky-900/80 text-white px-2 py-0.5 rounded">
                            UNet Mask: Proximal Tibia + Soft Tissue
                          </span>
                        </div>
                      )}
                    </div>
                  ) : (
                    <div className="text-center space-y-2 p-6">
                      <div className="w-12 h-12 rounded-full bg-sky-50 text-sky-600 flex items-center justify-center mx-auto">
                        <ScanIcon className="w-6 h-6" />
                      </div>
                      <p className="text-xs font-bold text-slate-700">No custom image uploaded yet</p>
                      <p className="text-[11px] text-slate-500">Click browse above to upload any knee AP X-ray file or switch to Presets.</p>
                    </div>
                  )}
                </div>
              </div>
            ) : (
              /* Preset Selection Cards */
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {CLINICAL_PRESETS.map((preset) => {
                  const isSelected = selectedPreset.id === preset.id;
                  return (
                    <button
                      key={preset.id}
                      type="button"
                      onClick={() => handleSelectPreset(preset)}
                      className={`p-4 rounded-2xl border text-left transition-all relative ${
                        isSelected
                          ? "bg-sky-50/70 border-sky-500 ring-2 ring-sky-500/20 shadow-md"
                          : "bg-white border-slate-200 hover:border-sky-300 hover:bg-slate-50"
                      }`}
                    >
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-xs font-bold text-slate-900">{preset.title}</span>
                        {isSelected && (
                          <span className="px-2 py-0.5 rounded-full bg-sky-600 text-white text-[10px] font-bold">
                            Active
                          </span>
                        )}
                      </div>
                      <p className="text-xs text-slate-600 mb-2">{preset.description}</p>
                      <div className="text-[11px] text-slate-500 flex justify-between border-t border-slate-100 pt-2">
                        <span>Age: {preset.age}y ({preset.sex})</span>
                        <span className="font-semibold text-slate-700">Grip: {preset.gripStrength} kg</span>
                      </div>
                    </button>
                  );
                })}
              </div>
            )}
          </div>

          {/* STEP 2 & 3: GRID WITH HANDGRIP CALCULATION + MULTIMODAL INFERENCE */}
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 border-t border-slate-100 pt-8">
            
            {/* LEFT COLUMN: Patient Demographics & Handgrip Trials */}
            <div className="lg:col-span-6 space-y-6">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold uppercase tracking-wider text-slate-900 flex items-center gap-2">
                  <ActivityIcon className="w-4 h-4 text-sky-600" />
                  Step 2: Manual Handgrip Dynamometer Entry
                </span>

                <div className="inline-flex p-1 rounded-xl bg-slate-100 border border-slate-200 text-[11px] font-bold">
                  <button
                    type="button"
                    onClick={() => setGripInputMode("detailed")}
                    className={`px-3 py-1 rounded-lg transition-all ${
                      gripInputMode === "detailed" ? "bg-sky-600 text-white" : "text-slate-600"
                    }`}
                  >
                    3-Trial Standard
                  </button>
                  <button
                    type="button"
                    onClick={() => setGripInputMode("direct")}
                    className={`px-3 py-1 rounded-lg transition-all ${
                      gripInputMode === "direct" ? "bg-sky-600 text-white" : "text-slate-600"
                    }`}
                  >
                    Quick Slider
                  </button>
                </div>
              </div>

              {/* 3-Trial dynamometer inputs */}
              {gripInputMode === "detailed" ? (
                <div className="space-y-4 p-4 rounded-2xl bg-slate-50 border border-slate-200">
                  {/* Left Hand Trials */}
                  <div>
                    <div className="flex justify-between items-center mb-1.5">
                      <span className="text-xs font-bold text-slate-700">Left Hand Force (3 Trials in kg)</span>
                      <span className="text-xs font-semibold text-sky-700">
                        Max: {Math.max(...leftTrials)} kg
                      </span>
                    </div>
                    <div className="grid grid-cols-3 gap-2">
                      {leftTrials.map((val, idx) => (
                        <div key={`left-${idx}`}>
                          <label className="text-[10px] text-slate-600 block mb-0.5">Trial {idx + 1}</label>
                          <input
                            type="number"
                            step="0.1"
                            value={val}
                            onChange={(e) => handleUpdateTrial("left", idx, parseFloat(e.target.value) || 0)}
                            className="w-full px-3 py-2 rounded-xl bg-white border border-slate-300 text-xs font-bold text-slate-900 focus:outline-none focus:ring-2 focus:ring-sky-500"
                          />
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Right Hand Trials */}
                  <div>
                    <div className="flex justify-between items-center mb-1.5">
                      <span className="text-xs font-bold text-slate-700">Right Hand Force (3 Trials in kg)</span>
                      <span className="text-xs font-semibold text-sky-700">
                        Max: {Math.max(...rightTrials)} kg
                      </span>
                    </div>
                    <div className="grid grid-cols-3 gap-2">
                      {rightTrials.map((val, idx) => (
                        <div key={`right-${idx}`}>
                          <label className="text-[10px] text-slate-600 block mb-0.5">Trial {idx + 1}</label>
                          <input
                            type="number"
                            step="0.1"
                            value={val}
                            onChange={(e) => handleUpdateTrial("right", idx, parseFloat(e.target.value) || 0)}
                            className="w-full px-3 py-2 rounded-xl bg-white border border-slate-300 text-xs font-bold text-slate-900 focus:outline-none focus:ring-2 focus:ring-sky-500"
                          />
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              ) : (
                /* Direct Grip Strength Slider */
                <div className="p-4 rounded-2xl bg-slate-50 border border-slate-200 space-y-2">
                  <div className="flex justify-between items-center">
                    <span className="text-xs font-bold text-slate-700">Peak Handgrip Force</span>
                    <span className="text-sm font-extrabold text-sky-700">{directGrip} kg</span>
                  </div>
                  <input
                    type="range"
                    min="5"
                    max="65"
                    step="0.5"
                    value={directGrip}
                    onChange={(e) => setDirectGrip(parseFloat(e.target.value))}
                    className="w-full accent-sky-600"
                  />
                  <div className="flex justify-between text-[10px] text-slate-600">
                    <span>5 kg (Severe)</span>
                    <span>AWGS Cutoff: {gripCutoff} kg</span>
                    <span>65 kg (Athletic)</span>
                  </div>
                </div>
              )}

              {/* Patient Basic Demographics & BMI Calculator */}
              <div className="p-4 rounded-2xl bg-slate-50 border border-slate-200 space-y-3">
                <span className="text-xs font-bold text-slate-700 block">
                  Patient Biomarkers &amp; BMI Auto-Calculation
                </span>
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                  <div>
                    <label className="text-[10px] text-slate-600 block mb-0.5">Age</label>
                    <input
                      type="number"
                      value={age}
                      onChange={(e) => setAge(parseInt(e.target.value) || 60)}
                      className="w-full px-3 py-1.5 rounded-xl bg-white border border-slate-300 text-xs font-bold text-slate-900 focus:ring-2 focus:ring-sky-500"
                    />
                  </div>

                  <div>
                    <label className="text-[10px] text-slate-600 block mb-0.5">Sex</label>
                    <select
                      value={sex}
                      onChange={(e) => setSex(e.target.value)}
                      className="w-full px-2 py-1.5 rounded-xl bg-white border border-slate-300 text-xs font-bold text-slate-900 focus:ring-2 focus:ring-sky-500"
                    >
                      <option value="Female">Female (&lt;18kg)</option>
                      <option value="Male">Male (&lt;28kg)</option>
                    </select>
                  </div>

                  <div>
                    <label className="text-[10px] text-slate-600 block mb-0.5">Height (cm)</label>
                    <input
                      type="number"
                      value={height}
                      onChange={(e) => setHeight(parseInt(e.target.value) || 160)}
                      className="w-full px-3 py-1.5 rounded-xl bg-white border border-slate-300 text-xs font-bold text-slate-900 focus:ring-2 focus:ring-sky-500"
                    />
                  </div>

                  <div>
                    <label className="text-[10px] text-slate-600 block mb-0.5">Weight (kg)</label>
                    <input
                      type="number"
                      value={weight}
                      onChange={(e) => setWeight(parseInt(e.target.value) || 60)}
                      className="w-full px-3 py-1.5 rounded-xl bg-white border border-slate-300 text-xs font-bold text-slate-900 focus:ring-2 focus:ring-sky-500"
                    />
                  </div>
                </div>

                {/* BMI & AWGS Assessment Badges */}
                <div className="flex flex-wrap items-center gap-2 pt-1 text-xs">
                  <span className="px-2.5 py-1 rounded-lg bg-white border border-slate-200 font-bold text-slate-700">
                    BMI: {calculatedBMI} kg/m² {calculatedBMI < 18.5 ? "· (Underweight)" : calculatedBMI > 25 ? "· (Overweight)" : "· (Normal)"}
                  </span>
                  <span
                    className={`px-2.5 py-1 rounded-lg font-bold border ${
                      isGripDeficient
                        ? "bg-rose-50 text-rose-700 border-rose-200"
                        : "bg-emerald-50 text-emerald-700 border-emerald-200"
                    }`}
                  >
                    {isGripDeficient
                      ? `AWGS Deficit: -${gripDeficitMargin} kg below cutoff`
                      : "AWGS Grip: Normal Strength"}
                  </span>
                </div>
              </div>
            </div>

            {/* RIGHT COLUMN: Identified Clinical Risk Tiers (AI Model Results) */}
            <div className="lg:col-span-6 space-y-6">
              <div className="flex items-center justify-between">
                <div>
                  <span className="text-xs font-bold uppercase tracking-wider text-sky-600 block">
                    Multimodal Fusion Prediction
                  </span>
                  <h3 className="text-lg font-extrabold text-slate-900">
                    Identified Clinical Risk Tiers
                  </h3>
                </div>
                <span className="px-2.5 py-1 rounded-full bg-slate-100 text-slate-600 text-[11px] font-bold">
                  CPU Inference: 1.1s
                </span>
              </div>

              {isLoading ? (
                <PatientReportSkeleton />
              ) : (
                <div className="space-y-4">
                  {/* Primary Sarcopenia Tier Card */}
                  <div className={`p-5 rounded-2xl border ${sarcopeniaColor} transition-all`}>
                    <div className="flex items-start justify-between gap-4">
                      <div>
                        <span className="text-[11px] font-bold uppercase tracking-wider opacity-80">
                          Sarcopenia Screening Stage
                        </span>
                        <h4 className="text-2xl font-black mt-0.5">
                          {doctorOverride ? overrideStage : computedSarcopeniaStage}
                        </h4>
                        <p className="text-xs mt-1 opacity-90">
                          Fusion Probability: <strong>{computedSarcopeniaScore}%</strong> · Based on Peak Grip ({peakCalculatedGrip} kg) + X-Ray Ratio ({softTissueRatio})
                        </p>
                      </div>
                      <div className="p-2 rounded-xl bg-white/60 shadow-sm">
                        <ActivityIcon className="w-6 h-6" />
                      </div>
                    </div>
                  </div>

                  {/* Osteoporosis Risk Tier Card */}
                  <div className={`p-5 rounded-2xl border ${osteoColor} transition-all`}>
                    <div className="flex items-start justify-between gap-4">
                      <div>
                        <span className="text-[11px] font-bold uppercase tracking-wider opacity-80">
                          Osteoporosis Risk Tier (Proximal Tibia)
                        </span>
                        <h4 className="text-xl font-black mt-0.5">
                          {computedOsteoRisk} ({computedOsteoProb}%)
                        </h4>
                        <p className="text-xs mt-1 opacity-90">
                          Trabecular bone mineral proxy calculated from subchondral tibia cortical index.
                        </p>
                      </div>
                      <div className="p-2 rounded-xl bg-white/60 shadow-sm">
                        <BoneIcon className="w-6 h-6" />
                      </div>
                    </div>
                  </div>

                  {/* Feature Contribution Breakdown */}
                  <div className="p-4 rounded-2xl bg-slate-50 border border-slate-200 space-y-3">
                    <span className="text-xs font-bold text-slate-700 block">
                      Evaluated Feature Contributions
                    </span>
                    <div className="space-y-2 text-xs">
                      <div>
                        <div className="flex justify-between text-[11px] text-slate-600 mb-1">
                          <span>Peak Handgrip Dynamometer ({peakCalculatedGrip} kg)</span>
                          <span className="font-bold text-slate-800">42% weight</span>
                        </div>
                        <div className="w-full bg-slate-200 h-2 rounded-full overflow-hidden">
                          <div className="bg-sky-600 h-full rounded-full" style={{ width: "42%" }} />
                        </div>
                      </div>

                      <div>
                        <div className="flex justify-between text-[11px] text-slate-600 mb-1">
                          <span>Thigh Soft-Tissue Muscle Ratio ({softTissueRatio})</span>
                          <span className="font-bold text-slate-800">36% weight</span>
                        </div>
                        <div className="w-full bg-slate-200 h-2 rounded-full overflow-hidden">
                          <div className="bg-sky-500 h-full rounded-full" style={{ width: "36%" }} />
                        </div>
                      </div>

                      <div>
                        <div className="flex justify-between text-[11px] text-slate-600 mb-1">
                          <span>Age &amp; BMI Index ({calculatedBMI} kg/m²)</span>
                          <span className="font-bold text-slate-800">22% weight</span>
                        </div>
                        <div className="w-full bg-slate-200 h-2 rounded-full overflow-hidden">
                          <div className="bg-slate-500 h-full rounded-full" style={{ width: "22%" }} />
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Clinician Override & Audit Trail Toggle */}
                  <div className="p-4 rounded-2xl bg-white border border-slate-200 space-y-3">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-bold text-slate-800">
                        Doctor Diagnostic Sign-off
                      </span>
                      <label className="flex items-center gap-2 text-xs font-semibold text-sky-700 cursor-pointer">
                        <input
                          type="checkbox"
                          checked={doctorOverride}
                          onChange={(e) => setDoctorOverride(e.target.checked)}
                          className="rounded border-slate-300 text-sky-600 focus:ring-sky-500"
                        />
                        <span>Enable Override</span>
                      </label>
                    </div>

                    {doctorOverride && (
                      <div className="space-y-2 pt-2 border-t border-slate-100">
                        <select
                          value={overrideStage}
                          onChange={(e) => setOverrideStage(e.target.value)}
                          className="w-full px-3 py-2 rounded-xl bg-slate-50 border border-slate-300 text-xs font-bold text-slate-800 focus:ring-2 focus:ring-sky-500"
                        >
                          <option value="No Sarcopenia">Override to: No Sarcopenia</option>
                          <option value="Possible Sarcopenia">Override to: Possible Sarcopenia</option>
                          <option value="Probable Sarcopenia">Override to: Probable Sarcopenia</option>
                          <option value="Severe Sarcopenia">Override to: Severe Sarcopenia</option>
                        </select>
                        <textarea
                          placeholder="Clinical reason for override (e.g., patient recovering from acute knee trauma)..."
                          value={doctorNotes}
                          onChange={(e) => setDoctorNotes(e.target.value)}
                          rows={2}
                          className="w-full p-2.5 rounded-xl bg-slate-50 border border-slate-300 text-xs text-slate-800 focus:ring-2 focus:ring-sky-500"
                        />
                      </div>
                    )}

                    <div className="flex items-center justify-between pt-2">
                      <button
                        type="button"
                        onClick={() => {
                          setShowExportSuccess(true);
                          setTimeout(() => setShowExportSuccess(false), 3000);
                        }}
                        className="px-4 py-2 rounded-xl bg-slate-900 hover:bg-slate-800 text-white font-bold text-xs transition-all flex items-center gap-2"
                      >
                        <FileTextIcon className="w-4 h-4" />
                        <span>Export Clinical Report</span>
                      </button>

                      {showExportSuccess && (
                        <span className="text-xs font-semibold text-emerald-600 flex items-center gap-1 animate-pulse">
                          <CheckCircleIcon className="w-4 h-4" />
                          <span>Report Generated Ready!</span>
                        </span>
                      )}
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>

      </div>
    </div>
  );
}
