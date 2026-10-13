"use client";

import React, { useEffect, useState } from "react";
import {
  ActivityIcon,
  BoneIcon,
  ScanIcon,
  SparklesIcon,
  CheckCircleIcon,
  CpuIcon,
  CrosshairIcon,
} from "@/components/Icons";

export interface PipelineStep {
  id: string;
  title: string;
  detail: string;
  metric: string;
  badge: string;
}

export const PIPELINE_STEPS: PipelineStep[] = [
  {
    id: "ingestion",
    title: "Radiograph Normalization & DICOM Ingestion",
    detail: "CLAHE contrast equalization, 512×512 tensor conversion, de-identification check.",
    metric: "Tensor: [1, 1, 512, 512] · 16-bit Float",
    badge: "PRE-PROCESSING",
  },
  {
    id: "segmentation",
    title: "Deep UNet Cortical Boundary Segmentation",
    detail: "Bilateral femoral condyle boundary localization & tibial plateau joint plane detection.",
    metric: "IoU: 0.942 · Joint Gap: 4.2mm",
    badge: "SEGMENTATION",
  },
  {
    id: "trabecular",
    title: "Proximal Tibia Trabecular Microarchitecture",
    detail: "Subchondral bone mineral proxy extraction & cortical thickness index evaluation.",
    metric: "Proximal Density Proxy: Evaluated",
    badge: "BONE MINERAL",
  },
  {
    id: "soft_tissue",
    title: "Thigh Soft-Tissue Compartment Volumetrics",
    detail: "Cross-sectional muscle-to-bone ratio extraction at 0.6× tibial plateau width.",
    metric: "Soft-to-Bone Ratio: Extracted",
    badge: "MUSCLE VOLUME",
  },
  {
    id: "fusion",
    title: "Multimodal Clinical Fusion & AWGS 2019 Staging",
    detail: "Correlating handgrip force, age, and BMI vectors with radiograph biomarkers.",
    metric: "Bayesian Multi-Modal Confidence: 94.8%",
    badge: "FUSION INFERENCE",
  },
];

interface AIProcessingVisualizerProps {
  isProcessing: boolean;
  imageSrc?: string | null;
  onComplete?: () => void;
  onSkip?: () => void;
  /** Custom duration for demo simulation in milliseconds (default 2400ms) */
  durationMs?: number;
  /** Optional external message from live screening wizard */
  externalMessage?: string;
  isModal?: boolean;
}

export function AIProcessingVisualizer({
  isProcessing,
  imageSrc,
  onComplete,
  onSkip,
  durationMs = 2400,
  externalMessage,
  isModal = false,
}: AIProcessingVisualizerProps) {
  if (!isProcessing) return null;

  return (
    <AIProcessingContent
      imageSrc={imageSrc}
      onComplete={onComplete}
      onSkip={onSkip}
      durationMs={durationMs}
      externalMessage={externalMessage}
      isModal={isModal}
    />
  );
}

function AIProcessingContent({
  imageSrc,
  onComplete,
  onSkip,
  durationMs = 2400,
  externalMessage,
  isModal = false,
}: Omit<AIProcessingVisualizerProps, "isProcessing">) {
  const [activeStepIndex, setActiveStepIndex] = useState(0);
  const [elapsedMs, setElapsedMs] = useState(0);
  const [telemetryLogs, setTelemetryLogs] = useState<string[]>([
    "▶ [0.00s] Initializing PyTorch runtime on CPU (4 inference threads)...",
    "▶ [0.08s] Radiograph ingestion: calibrating pixel resolution...",
  ]);

  useEffect(() => {
    const start = Date.now();
    const stepInterval = durationMs / PIPELINE_STEPS.length;

    const interval = setInterval(() => {
      const elapsed = Date.now() - start;
      setElapsedMs(elapsed);

      const calculatedIndex = Math.min(
        Math.floor(elapsed / stepInterval),
        PIPELINE_STEPS.length - 1
      );
      setActiveStepIndex(calculatedIndex);

      // Add dynamic telemetry logs based on progression
      if (calculatedIndex === 1 && elapsed >= stepInterval) {
        setTelemetryLogs((prev) =>
          prev.length < 3
            ? [
                ...prev,
                "▶ [0.48s] UNet-ResNet34 forward pass: segmenting cortical contours...",
                "▶ [0.65s] Joint space plane located at Y=268 px",
              ]
            : prev
        );
      } else if (calculatedIndex === 2 && elapsed >= stepInterval * 2) {
        setTelemetryLogs((prev) =>
          prev.length < 5
            ? [
                ...prev,
                "▶ [0.98s] Computing proximal tibia subchondral trabecular attenuation...",
                "▶ [1.18s] Cortical thickness index evaluated (Medial & Lateral)",
              ]
            : prev
        );
      } else if (calculatedIndex === 3 && elapsed >= stepInterval * 3) {
        setTelemetryLogs((prev) =>
          prev.length < 7
            ? [
                ...prev,
                "▶ [1.45s] Measuring thigh soft tissue margin at +0.6x plateau width...",
                "▶ [1.68s] Quadriceps & vastus lateralis cross-sectional area mapped",
              ]
            : prev
        );
      } else if (calculatedIndex === 4 && elapsed >= stepInterval * 4) {
        setTelemetryLogs((prev) =>
          prev.length < 9
            ? [
                ...prev,
                "▶ [1.95s] Correlating dynamometer force vector against AWGS cutoffs...",
                "▶ [2.15s] Generating Grad-CAM attention heatmaps & clinical risk tiers",
              ]
            : prev
        );
      }

      if (elapsed >= durationMs) {
        clearInterval(interval);
        if (onComplete) onComplete();
      }
    }, 50);

    return () => clearInterval(interval);
  }, [durationMs, onComplete]);
  const progressPercent = Math.min(100, Math.round((elapsedMs / durationMs) * 100));

  const content = (
    <div className="bg-slate-950 text-white rounded-3xl border border-sky-500/30 shadow-2xl overflow-hidden p-6 sm:p-8 space-y-6 max-w-4xl w-full mx-auto relative">
      {/* Background cybernetic grid lines */}
      <div className="absolute inset-0 bg-[radial-gradient(#0284c7_1px,transparent_1px)] [background-size:24px_24px] opacity-15 pointer-events-none" />

      {/* Header bar */}
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-800 pb-4 relative z-10">
        <div className="flex items-center gap-3">
          <div className="relative">
            <div className="w-10 h-10 rounded-xl bg-sky-500/20 border border-sky-400 flex items-center justify-center text-sky-400 animate-pulse">
              <CpuIcon className="w-5 h-5" />
            </div>
            <span className="absolute -top-1 -right-1 w-3 h-3 bg-emerald-500 rounded-full border-2 border-slate-950 animate-ping" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-base sm:text-lg font-bold tracking-tight text-white flex items-center gap-2">
                Multimodal AI Clinical Inference Engine
              </h3>
              <span className="text-[10px] font-mono uppercase px-2 py-0.5 rounded-full bg-sky-950 border border-sky-700/60 text-sky-300">
                ACTIVE PIPELINE
              </span>
            </div>
            <p className="text-xs text-slate-400">
              {externalMessage || "Executing real-time radiograph segmentation & AWGS 2019 risk fusion..."}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <div className="text-right">
            <span className="text-[10px] uppercase font-mono tracking-wider text-slate-500 block">
              COMPUTE TIME
            </span>
            <span className="text-sm font-mono font-bold text-sky-400">
              {(elapsedMs / 1000).toFixed(2)}s
            </span>
          </div>

          {onSkip && (
            <button
              type="button"
              onClick={onSkip}
              className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white text-xs font-semibold border border-slate-700 transition-colors"
            >
              Skip to Results &rarr;
            </button>
          )}
        </div>
      </div>

      {/* Main Grid: Live Scanning Preview + Step Tracker */}
      <div className="grid grid-cols-1 md:grid-cols-12 gap-6 relative z-10">
        {/* Left: Interactive Radiograph Scanner HUD */}
        <div className="md:col-span-5 flex flex-col items-center">
          <div className="relative w-full aspect-square max-w-[280px] rounded-2xl overflow-hidden bg-black border-2 border-sky-500/40 shadow-inner group">
            {/* Underlying radiograph image or fallback visualizer */}
            {imageSrc ? (
              <img
                src={imageSrc}
                alt="Radiograph being scanned by AI"
                className="w-full h-full object-contain filter contrast-125 opacity-80"
              />
            ) : (
              <div className="w-full h-full flex flex-col items-center justify-center p-4 text-center bg-slate-900/90">
                <ScanIcon className="w-12 h-12 text-sky-500/40 mb-2 animate-pulse" />
                <span className="text-xs font-mono text-slate-400">AP KNEE RADIOGRAPH</span>
                <span className="text-[10px] text-slate-500 mt-1">Matrix 512×512 Standard</span>
              </div>
            )}

            {/* Glowing Laser Scan Beam */}
            <div className="absolute inset-x-0 h-1.5 bg-gradient-to-r from-transparent via-cyan-400 to-transparent shadow-[0_0_15px_4px_rgba(6,182,212,0.8)] pointer-events-none animate-scanbeam" />

            {/* HUD Target Overlays & Crosshairs */}
            <div className="absolute inset-0 pointer-events-none p-3 flex flex-col justify-between">
              {/* Corner brackets */}
              <div className="flex justify-between">
                <div className="w-4 h-4 border-t-2 border-l-2 border-sky-400" />
                <div className="w-4 h-4 border-t-2 border-r-2 border-sky-400" />
              </div>

              {/* Floating Anatomical Landmark Tags */}
              <div className="space-y-1 font-mono text-[9px]">
                <div className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded bg-sky-950/80 border border-sky-500/50 text-cyan-300">
                  <CrosshairIcon className="w-2.5 h-2.5" />
                  <span>ROI 1: Femoral Condyle</span>
                </div>
                <br />
                <div className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded bg-amber-950/80 border border-amber-500/50 text-amber-300">
                  <ActivityIcon className="w-2.5 h-2.5" />
                  <span>ROI 2: Tibial Plateau Joint Line</span>
                </div>
                <br />
                <div className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded bg-emerald-950/80 border border-emerald-500/50 text-emerald-300">
                  <BoneIcon className="w-2.5 h-2.5" />
                  <span>ROI 3: Subchondral Trabecular Zone</span>
                </div>
              </div>

              <div className="flex justify-between items-end">
                <div className="w-4 h-4 border-b-2 border-l-2 border-sky-400" />
                <div className="text-[9px] font-mono text-cyan-400/90 bg-slate-950/80 px-1.5 py-0.5 rounded border border-cyan-800/40">
                  FOV: 180mm · 0.25mm/px
                </div>
                <div className="w-4 h-4 border-b-2 border-r-2 border-sky-400" />
              </div>
            </div>
          </div>

          <div className="flex items-center justify-between w-full max-w-[280px] mt-2 text-[10px] font-mono text-slate-400">
            <span>MODEL: UNet-ResNet34</span>
            <span className="text-emerald-400 flex items-center gap-1">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-ping" />
              INFERENCE ONLINE
            </span>
          </div>
        </div>

        {/* Right: Pipeline Steps Tracker & Live Telemetry Logs */}
        <div className="md:col-span-7 flex flex-col justify-between space-y-4">
          {/* Progress bar */}
          <div className="space-y-1.5">
            <div className="flex justify-between items-center text-xs font-mono">
              <span className="text-slate-400 flex items-center gap-1.5">
                <SparklesIcon className="w-3.5 h-3.5 text-sky-400" />
                <span>PIPELINE PROGRESS</span>
              </span>
              <span className="text-sky-400 font-bold">{progressPercent}%</span>
            </div>
            <div className="w-full h-2.5 bg-slate-900 rounded-full overflow-hidden border border-slate-800 p-0.5">
              <div
                className="h-full bg-gradient-to-r from-sky-500 via-cyan-400 to-emerald-400 rounded-full transition-all duration-150 ease-out shadow-[0_0_12px_rgba(56,189,248,0.5)]"
                style={{ width: `${progressPercent}%` }}
              />
            </div>
          </div>

          {/* Steps List */}
          <div className="space-y-2">
            {PIPELINE_STEPS.map((step, idx) => {
              const isPast = idx < activeStepIndex;
              const isCurrent = idx === activeStepIndex;

              return (
                <div
                  key={step.id}
                  className={`p-2.5 rounded-xl border text-xs transition-all duration-200 ${
                    isCurrent
                      ? "bg-sky-950/60 border-sky-500 text-white shadow-lg shadow-sky-950/50"
                      : isPast
                      ? "bg-slate-900/60 border-slate-800 text-slate-400"
                      : "bg-slate-950/40 border-slate-900 text-slate-600"
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      {isPast ? (
                        <CheckCircleIcon className="w-4 h-4 text-emerald-400 shrink-0" />
                      ) : isCurrent ? (
                        <div className="w-4 h-4 rounded-full border-2 border-sky-400 border-t-transparent animate-spin shrink-0" />
                      ) : (
                        <span className="w-4 h-4 rounded-full bg-slate-800 text-slate-500 text-[10px] font-bold flex items-center justify-center shrink-0">
                          {idx + 1}
                        </span>
                      )}
                      <span className={`font-semibold ${isCurrent ? "text-white" : ""}`}>
                        {step.title}
                      </span>
                    </div>

                    <span
                      className={`text-[9px] font-mono px-2 py-0.5 rounded-full ${
                        isCurrent
                          ? "bg-sky-500 text-slate-950 font-bold animate-pulse"
                          : isPast
                          ? "bg-slate-800 text-emerald-400"
                          : "bg-slate-900 text-slate-600"
                      }`}
                    >
                      {isPast ? "DONE" : isCurrent ? step.badge : "PENDING"}
                    </span>
                  </div>

                  {isCurrent && (
                    <div className="mt-1.5 pl-6 text-[11px] text-sky-200 flex flex-wrap justify-between gap-1">
                      <span>{step.detail}</span>
                      <span className="font-mono text-cyan-300 font-bold">{step.metric}</span>
                    </div>
                  )}
                </div>
              );
            })}
          </div>

          {/* Telemetry Log Terminal */}
          <div className="rounded-xl bg-black/80 border border-slate-800 p-2.5 font-mono text-[10px] text-slate-400 space-y-1 max-h-20 overflow-hidden shadow-inner">
            <div className="flex items-center justify-between text-[9px] text-slate-500 pb-1 border-b border-slate-900">
              <span>DIAGNOSTIC TELEMETRY STREAM</span>
              <span className="text-emerald-500">LIVE</span>
            </div>
            {telemetryLogs.slice(-3).map((log, idx) => (
              <div key={idx} className="truncate text-cyan-400/90">
                {log}
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );

  if (isModal) {
    return (
      <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-md animate-in fade-in duration-200">
        {content}
      </div>
    );
  }

  return content;
}
