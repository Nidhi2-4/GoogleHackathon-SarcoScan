import React from "react";
import Link from "next/link";
import {
  ActivityIcon,
  BoneIcon,
  ScanIcon,
  ShieldCheckIcon,
  SparklesIcon,
  PhoneIcon,
  MailIcon,
  UsersIcon,
  ServerIcon,
  CheckCircleIcon,
  ArrowRightIcon,
} from "@/components/Icons";

export const metadata = {
  title: "About SarcoScan · On-Premise AI Clinical Screening",
  description: "Learn about SarcoScan, the on-premise AI screening tool combining routine knee AP X-rays with handgrip strength for early sarcopenia and osteoporosis triage.",
};

export default function AboutPage() {
  return (
    <div className="py-12 px-4 sm:px-8 max-w-6xl mx-auto space-y-16">
      {/* Hero Section */}
      <div className="relative overflow-hidden rounded-3xl bg-white border border-slate-200 shadow-xl shadow-sky-900/5 p-8 sm:p-14 space-y-6">
        <h1 className="text-3xl sm:text-5xl font-extrabold tracking-tight text-slate-900 leading-tight">
          Democratizing Musculoskeletal & <span className="text-sky-600">Sarcopenia Screening</span>
        </h1>
        <p className="text-base sm:text-lg text-slate-600 max-w-3xl leading-relaxed">
          SarcoScan combines two diagnostic tests already performed routinely in community and rural hospitals—a <strong>routine knee AP radiograph</strong> and a <strong>10-second handgrip test</strong>—to detect sarcopenia and osteoporosis risk years before a catastrophic fall occurs.
        </p>

        <div className="flex flex-wrap gap-4 pt-4">
          <Link
            href="/#screening-demo"
            className="px-6 py-3.5 rounded-xl bg-sky-600 hover:bg-sky-700 text-white font-semibold text-sm transition-all shadow-md shadow-sky-600/20 inline-flex items-center gap-2"
          >
            <span>Launch Live Screening Demo</span>
            <ArrowRightIcon className="w-4 h-4" />
          </Link>
          <a
            href="tel:+18005557272"
            className="px-6 py-3.5 rounded-xl bg-slate-50 hover:bg-slate-100 border border-slate-200 text-slate-800 font-semibold text-sm transition-all inline-flex items-center gap-2"
          >
            <PhoneIcon className="w-4 h-4 text-sky-600" />
            <span>Speak with Research Team</span>
          </a>
        </div>
      </div>

      {/* The Problem & The Solution */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        <div className="p-8 rounded-3xl bg-slate-50 border border-slate-200 space-y-4 shadow-sm">
          <div className="w-12 h-12 rounded-2xl bg-sky-100 text-sky-700 flex items-center justify-center shadow-sm">
            <BoneIcon className="w-6 h-6" />
          </div>
          <h2 className="text-2xl font-bold text-slate-900">The Clinical Dilemma</h2>
          <p className="text-sm text-slate-600 leading-relaxed">
            Sarcopenia (age-related loss of skeletal muscle mass and functional strength) is critically under-diagnosed in elderly populations. Gold-standard confirmation requires dual-energy X-ray absorptiometry (DEXA) or whole-body CT scans, which most Tier-2 and Tier-3 hospitals simply do not possess. As a result, patients are typically identified only after experiencing a fragility fracture.
          </p>
        </div>

        <div className="p-8 rounded-3xl bg-sky-50/70 border border-sky-200 space-y-4 shadow-sm">
          <div className="w-12 h-12 rounded-2xl bg-sky-600 text-white flex items-center justify-center shadow-md shadow-sky-600/20">
            <ActivityIcon className="w-6 h-6" />
          </div>
          <h2 className="text-2xl font-bold text-slate-900">The SarcoScan Solution</h2>
          <p className="text-sm text-slate-700 leading-relaxed">
            Hospitals already routinely capture knee radiographs for joint pain and measure grip strength. SarcoScan uses deep learning to segment femur, tibia, and soft tissue from the knee AP X-ray, computes soft-tissue-to-bone cross ratios, and fuses them with grip dynamics to yield an instant risk stratification.
          </p>
        </div>
      </div>

      {/* 4-Step Pipeline */}
      <div className="bg-white rounded-3xl border border-slate-200 p-8 sm:p-12 space-y-8 shadow-sm">
        <div className="text-center max-w-2xl mx-auto space-y-2">
          <span className="text-xs font-bold uppercase tracking-wider text-sky-600">How It Works</span>
          <h2 className="text-3xl font-extrabold text-slate-900">The 4-Step Screening Pipeline</h2>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
          <div className="p-5 rounded-2xl bg-slate-50 border border-slate-200 space-y-3">
            <div className="w-8 h-8 rounded-lg bg-sky-100 font-bold text-sm flex items-center justify-center text-sky-700">
              1
            </div>
            <h3 className="font-bold text-base text-slate-900">Data Ingestion</h3>
            <p className="text-xs text-slate-600 leading-relaxed">
              Technician registers patient, enters 3 handgrip trials per hand, and uploads standard knee AP DICOM or image.
            </p>
          </div>

          <div className="p-5 rounded-2xl bg-slate-50 border border-slate-200 space-y-3">
            <div className="w-8 h-8 rounded-lg bg-sky-200 font-bold text-sm flex items-center justify-center text-sky-800">
              2
            </div>
            <h3 className="font-bold text-base text-slate-900">AI Segmentation</h3>
            <p className="text-xs text-slate-600 leading-relaxed">
              U-Net neural network segments bone vs soft tissue and calculates precise thigh-to-calf muscle thickness ratios.
            </p>
          </div>

          <div className="p-5 rounded-2xl bg-slate-50 border border-slate-200 space-y-3">
            <div className="w-8 h-8 rounded-lg bg-sky-600 font-bold text-sm flex items-center justify-center text-white">
              3
            </div>
            <h3 className="font-bold text-base text-slate-900">Multimodal Fusion</h3>
            <p className="text-xs text-slate-600 leading-relaxed">
              Gradient-boosted fusion model combines image features with AWGS 2019 grip thresholds, age, sex, and BMI.
            </p>
          </div>

          <div className="p-5 rounded-2xl bg-slate-50 border border-slate-200 space-y-3">
            <div className="w-8 h-8 rounded-lg bg-sky-800 font-bold text-sm flex items-center justify-center text-white">
              4
            </div>
            <h3 className="font-bold text-base text-slate-900">Clinical Triage</h3>
            <p className="text-xs text-slate-600 leading-relaxed">
              Doctor receives stage (No / Possible / Probable / Severe), osteoporosis risk tier, explainable heatmap, and PDF report.
            </p>
          </div>
        </div>
      </div>

      {/* Target Validation Metrics Table */}
      <div className="bg-slate-50 rounded-3xl border border-slate-200 p-8 sm:p-12 space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h2 className="text-2xl font-bold text-slate-900">Pilot Validation Targets</h2>
            <p className="text-xs text-slate-500">Empirical milestones targeted for clinical pilot trials</p>
          </div>
          <span className="px-3 py-1 rounded-full bg-sky-100 text-xs font-bold text-sky-800 border border-sky-200">
            Benchmarked on CPU Only
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm bg-white rounded-2xl overflow-hidden border border-slate-200 shadow-sm">
            <thead className="bg-sky-50 text-slate-800 font-bold text-xs uppercase tracking-wider border-b border-slate-200">
              <tr>
                <th className="p-4">Clinical Metric</th>
                <th className="p-4">Target Standard</th>
                <th className="p-4">Validation Method</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 text-slate-700">
              <tr>
                <td className="p-4 font-semibold text-slate-900">Fusion Model AUC vs Grip Alone</td>
                <td className="p-4 text-sky-700 font-bold">Statistically Higher</td>
                <td className="p-4 text-xs text-slate-500">DeLong paired test (p &lt; 0.05)</td>
              </tr>
              <tr className="bg-slate-50/50">
                <td className="p-4 font-semibold text-slate-900">Screening Sensitivity</td>
                <td className="p-4 text-sky-700 font-bold">85% or higher</td>
                <td className="p-4 text-xs text-slate-500">Screening threshold against reference DEXA</td>
              </tr>
              <tr>
                <td className="p-4 font-semibold text-slate-900">Osteoporosis Risk AUC</td>
                <td className="p-4 text-sky-700 font-bold">0.80 or higher</td>
                <td className="p-4 text-xs text-slate-500">Proximal tibia radiograph vs DXA T-scores</td>
              </tr>
              <tr className="bg-slate-50/50">
                <td className="p-4 font-semibold text-slate-900">Inference Time</td>
                <td className="p-4 font-bold text-slate-900">Under 5.0 seconds</td>
                <td className="p-4 text-xs text-slate-500">Standard Intel i5 CPU, 16GB RAM, no GPU required</td>
              </tr>
              <tr>
                <td className="p-4 font-semibold text-slate-900">Total Workflow Time Per Patient</td>
                <td className="p-4 font-bold text-slate-900">Under 5 minutes</td>
                <td className="p-4 text-xs text-slate-500">Registration to printable clinician report</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      {/* Clinical Research Team Contact & Direct Links */}
      <div className="bg-white rounded-3xl border border-slate-200 p-8 sm:p-12 space-y-6 shadow-sm">
        <div className="flex items-center gap-3">
          <div className="p-3 rounded-2xl bg-sky-100 text-sky-700">
            <UsersIcon className="w-6 h-6" />
          </div>
          <div>
            <h2 className="text-2xl font-bold text-slate-900">Connect with Clinical Research Team</h2>
            <p className="text-xs text-slate-500">AI Developers & Medical Technology Researchers</p>
          </div>
        </div>

        <p className="text-sm text-slate-600 leading-relaxed">
          Interested in bringing SarcoScan to your hospital or clinic for clinical trials? Reach out to our engineering and medical liaisons:
        </p>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-2">
          <a
            href="tel:+18005557272"
            className="p-4 rounded-2xl bg-slate-50 hover:bg-slate-100 border border-slate-200 flex items-center gap-4 transition-all shadow-sm"
          >
            <div className="p-3 rounded-xl bg-sky-600 text-white">
              <PhoneIcon className="w-5 h-5" />
            </div>
            <div>
              <span className="text-xs text-slate-500">Toll-Free Clinical Support</span>
              <p className="font-bold text-slate-900 text-base">+1 (800) 555-7272</p>
            </div>
          </a>

          <a
            href="mailto:support@sarcoscan.ai"
            className="p-4 rounded-2xl bg-slate-50 hover:bg-slate-100 border border-slate-200 flex items-center gap-4 transition-all shadow-sm"
          >
            <div className="p-3 rounded-xl bg-sky-100 text-sky-700">
              <MailIcon className="w-5 h-5" />
            </div>
            <div>
              <span className="text-xs text-slate-500">Email Project Team</span>
              <p className="font-bold text-slate-900 text-base">support@sarcoscan.ai</p>
            </div>
          </a>
        </div>
      </div>
    </div>
  );
}
