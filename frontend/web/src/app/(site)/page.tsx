import type { Metadata } from "next";
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
  ServerIcon,
  UsersIcon,
  FileTextIcon,
  InfoIcon,
} from "@/components/Icons";

export const metadata: Metadata = {
  title: "SarcoScan · On-Premise AI Screening for Sarcopenia & Osteoporosis",
  description:
    "An on-premise AI clinical triage platform that turns routine knee AP radiographs and a 10-second handgrip test into immediate sarcopenia & osteoporosis risk stratifications—no DEXA or CT needed.",
  keywords: [
    "Sarcopenia AI Screening",
    "Knee AP X-Ray Analysis",
    "Handgrip Strength AWGS 2019",
    "Osteoporosis Risk Stratification",
    "On-Premise Clinical AI",
    "Hospital LAN AI Triage",
    "SarcoScan",
  ],
  openGraph: {
    title: "SarcoScan · On-Premise AI Screening for Sarcopenia & Osteoporosis",
    description:
      "Rapid AI clinical triage platform turning routine knee AP radiographs and handgrip tests into immediate risk stratifications.",
    url: "https://sarcoscan.ai",
    siteName: "SarcoScan",
    type: "website",
  },
  twitter: {
    card: "summary_large_image",
    title: "SarcoScan · AI Clinical Triage Platform",
    description:
      "Rapid multimodal screening for sarcopenia and osteoporosis with routine knee X-rays and handgrip dynamometer tests.",
  },
};

export default function HomePage() {
  return (
    <div className="bg-slate-50/50">

      {/* 1. HERO SECTION (Full-Screen Clean Above-The-Fold) */}
      <section className="min-h-[calc(100vh-64px)] flex flex-col items-center justify-center px-4 sm:px-8 max-w-5xl mx-auto text-center py-12">
        <div className="space-y-6 max-w-4xl mx-auto">
          <h1 className="text-4xl sm:text-6xl lg:text-7xl font-extrabold tracking-tight text-slate-900 leading-[1.12]">
            Knee X-Ray + Handgrip AI<br className="hidden sm:inline" /> Screening for <span className="text-sky-600">Sarcopenia</span>
          </h1>

          <p className="text-base sm:text-xl text-slate-600 leading-relaxed max-w-3xl mx-auto font-normal">
            An on-premise AI clinical triage platform that turns routine knee AP radiographs and a 10-second handgrip test into immediate sarcopenia &amp; osteoporosis risk stratifications—<strong>no DEXA or CT needed</strong>.
          </p>

          {/* Action Buttons */}
          <div className="flex flex-wrap items-center justify-center gap-4 pt-4">
            <Link
              href="/demo"
              className="px-8 py-4 rounded-2xl bg-sky-600 hover:bg-sky-700 text-white font-bold text-sm transition-all shadow-xl shadow-sky-600/25 inline-flex items-center gap-2 hover:scale-[1.02]"
            >
              <span>Upload X-Ray &amp; Test AI</span>
              <ArrowRightIcon className="w-4 h-4" />
            </Link>
          </div>
        </div>
      </section>

      <div className="space-y-24 pb-24">

        {/* 2. THREE DEDICATED CLINICAL PANELS (Doctor, Technician/Nurse, Patient) */}
        <section className="px-4 sm:px-8 max-w-7xl mx-auto">
          <div className="text-center space-y-3 mb-12">
            <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-sky-50 border border-sky-200 text-xs font-bold text-sky-700">
              <UsersIcon className="w-4 h-4" />
              <span>Role-Based Clinical Workflow</span>
            </div>
            <h2 className="text-3xl sm:text-4xl font-extrabold text-slate-900 tracking-tight">
              Tailored Portals for the Entire Care Team
            </h2>
            <p className="text-sm sm:text-base text-slate-600 max-w-2xl mx-auto">
              SarcoScan provides purpose-built interfaces for every tier of clinical operations—from radiographer intake to diagnostic sign-off and patient education.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">

            {/* Panel 1: Doctor & Clinician */}
            <div className="p-8 rounded-3xl bg-white border border-slate-200 shadow-lg shadow-sky-900/5 hover:border-sky-300 transition-all flex flex-col justify-between group">
              <div className="space-y-5">
                <div className="w-14 h-14 rounded-2xl bg-sky-50 border border-sky-100 flex items-center justify-center text-sky-600 group-hover:scale-110 transition-transform">
                  <ActivityIcon className="w-7 h-7" />
                </div>
                <div>
                  <span className="text-[11px] font-bold uppercase tracking-wider text-sky-600 block mb-1">
                    Physician &amp; Specialist Portal
                  </span>
                  <h3 className="text-xl font-bold text-slate-900">Doctor &amp; Clinician Panel</h3>
                </div>
                <p className="text-xs sm:text-sm text-slate-600 leading-relaxed">
                  Instant diagnostic triage view with AWGS 2019 criteria validation, confidence probabilities, doctor override controls, and digital report sign-off.
                </p>
                <ul className="space-y-2 text-xs text-slate-700">
                  <li className="flex items-center gap-2">
                    <CheckCircleIcon className="w-4 h-4 text-sky-600 shrink-0" />
                    <span>Multimodal sarcopenia &amp; osteoporosis staging</span>
                  </li>
                  <li className="flex items-center gap-2">
                    <CheckCircleIcon className="w-4 h-4 text-sky-600 shrink-0" />
                    <span>Physician audit trail &amp; clinical override notes</span>
                  </li>
                  <li className="flex items-center gap-2">
                    <CheckCircleIcon className="w-4 h-4 text-sky-600 shrink-0" />
                    <span>1-click signed PDF clinical triage reports</span>
                  </li>
                </ul>
              </div>
              <div className="pt-6 mt-6 border-t border-slate-100">
                <Link
                  href="/login"
                  className="inline-flex items-center gap-2 text-xs font-bold text-sky-600 hover:text-sky-700"
                >
                  <span>Access Doctor Portal</span>
                  <ArrowRightIcon className="w-3.5 h-3.5" />
                </Link>
              </div>
            </div>

            {/* Panel 2: Technician & Nurse */}
            <div className="p-8 rounded-3xl bg-white border border-slate-200 shadow-lg shadow-sky-900/5 hover:border-sky-300 transition-all flex flex-col justify-between group">
              <div className="space-y-5">
                <div className="w-14 h-14 rounded-2xl bg-sky-50 border border-sky-100 flex items-center justify-center text-sky-600 group-hover:scale-110 transition-transform">
                  <ScanIcon className="w-7 h-7" />
                </div>
                <div>
                  <span className="text-[11px] font-bold uppercase tracking-wider text-sky-600 block mb-1">
                    Intake &amp; Radiography Station
                  </span>
                  <h3 className="text-xl font-bold text-slate-900">Technician / Nurse Station</h3>
                </div>
                <p className="text-xs sm:text-sm text-slate-600 leading-relaxed">
                  Streamlined 10-second intake interface. Drag-and-drop routine knee AP radiographs, log 3-trial BLE dynamometer force, and run automated image QC checks.
                </p>
                <ul className="space-y-2 text-xs text-slate-700">
                  <li className="flex items-center gap-2">
                    <CheckCircleIcon className="w-4 h-4 text-sky-600 shrink-0" />
                    <span>Rapid DICOM drag &amp; drop / PACS sync</span>
                  </li>
                  <li className="flex items-center gap-2">
                    <CheckCircleIcon className="w-4 h-4 text-sky-600 shrink-0" />
                    <span>BLE digital handgrip dynamometer pairing</span>
                  </li>
                  <li className="flex items-center gap-2">
                    <CheckCircleIcon className="w-4 h-4 text-sky-600 shrink-0" />
                    <span>Automated knee AP crop &amp; exposure validation</span>
                  </li>
                </ul>
              </div>
              <div className="pt-6 mt-6 border-t border-slate-100">
                <Link
                  href="/login"
                  className="inline-flex items-center gap-2 text-xs font-bold text-sky-600 hover:text-sky-700"
                >
                  <span>Launch Nurse Station</span>
                  <ArrowRightIcon className="w-3.5 h-3.5" />
                </Link>
              </div>
            </div>

            {/* Panel 3: Patient Summary */}
            <div className="p-8 rounded-3xl bg-white border border-slate-200 shadow-lg shadow-sky-900/5 hover:border-sky-300 transition-all flex flex-col justify-between group">
              <div className="space-y-5">
                <div className="w-14 h-14 rounded-2xl bg-sky-50 border border-sky-100 flex items-center justify-center text-sky-600 group-hover:scale-110 transition-transform">
                  <BoneIcon className="w-7 h-7" />
                </div>
                <div>
                  <span className="text-[11px] font-bold uppercase tracking-wider text-sky-600 block mb-1">
                    Patient Engagement
                  </span>
                  <h3 className="text-xl font-bold text-slate-900">Patient Health Portal</h3>
                </div>
                <p className="text-xs sm:text-sm text-slate-600 leading-relaxed">
                  Accessible, plain-language risk breakdowns that demystify sarcopenia and osteoporosis, providing actionable nutrition, protein, and resistance guidance.
                </p>
                <ul className="space-y-2 text-xs text-slate-700">
                  <li className="flex items-center gap-2">
                    <CheckCircleIcon className="w-4 h-4 text-sky-600 shrink-0" />
                    <span>Non-stigmatizing color-coded risk tiers</span>
                  </li>
                  <li className="flex items-center gap-2">
                    <CheckCircleIcon className="w-4 h-4 text-sky-600 shrink-0" />
                    <span>Personalized protein &amp; resistance exercise tips</span>
                  </li>
                  <li className="flex items-center gap-2">
                    <CheckCircleIcon className="w-4 h-4 text-sky-600 shrink-0" />
                    <span>Clear DEXA referral guidance when flagged</span>
                  </li>
                </ul>
              </div>
              <div className="pt-6 mt-6 border-t border-slate-100">
                <Link
                  href="/demo"
                  className="inline-flex items-center gap-2 text-xs font-bold text-sky-600 hover:text-sky-700"
                >
                  <span>View Sample Patient Report</span>
                  <ArrowRightIcon className="w-3.5 h-3.5" />
                </Link>
              </div>
            </div>

          </div>
        </section>

        {/* 3. INTERACTIVE DEMO CTA BANNER */}
        <section className="px-4 sm:px-8 max-w-7xl mx-auto">
          <div className="p-8 sm:p-12 rounded-3xl bg-gradient-to-br from-sky-600 to-sky-800 text-white shadow-xl shadow-sky-600/20 flex flex-col md:flex-row items-center justify-between gap-8">
            <div className="space-y-3 max-w-2xl">
              <span className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-white/15 text-xs font-bold text-white border border-white/20">
                <SparklesIcon className="w-3.5 h-3.5" />
                <span>Live Interactive Sandbox</span>
              </span>
              <h2 className="text-2xl sm:text-3xl font-extrabold text-white">
                Test the AI Engine with Custom X-Rays or Presets
              </h2>
              <p className="text-sm text-sky-100 leading-relaxed">
                Experience our real-time inference calculator: upload knee radiographs, adjust 3-trial dynamometer force, compute BMI, and view multimodal risk classifications.
              </p>
            </div>

            <Link
              href="/demo"
              className="px-8 py-4 rounded-2xl bg-white hover:bg-slate-100 text-sky-800 font-bold text-sm transition-all shadow-lg hover:scale-105 shrink-0 flex items-center gap-2"
            >
              <span>Launch Live Demo Station</span>
              <ArrowRightIcon className="w-4 h-4 text-sky-600" />
            </Link>
          </div>
        </section>

        {/* 4. CLINICAL PIPELINE (HOW IT WORKS IN 3 STEPS) */}
        <section className="px-4 sm:px-8 max-w-7xl mx-auto">
          <div className="text-center space-y-3 mb-14">
            <span className="text-xs font-bold uppercase tracking-wider text-sky-600">
              Validated Clinical Workflow
            </span>
            <h2 className="text-3xl sm:text-4xl font-extrabold text-slate-900 tracking-tight">
              From Routine Knee Radiograph to Dual Risk Staging
            </h2>
            <p className="text-sm sm:text-base text-slate-600 max-w-2xl mx-auto">
              How SarcoScan transforms standard primary care clinic visits into comprehensive musculoskeletal screenings in under 60 seconds.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <div className="p-8 rounded-3xl bg-white border border-slate-200 shadow-md space-y-4 relative">
              <span className="text-4xl font-black text-sky-600">01</span>
              <h3 className="text-xl font-bold text-slate-900">Knee AP Segmentation</h3>
              <p className="text-xs sm:text-sm text-slate-600 leading-relaxed">
                UNet model segments thigh muscle vs. cortical bone to extract the soft-tissue-to-bone ratio and proximal tibia trabecular proxy without extra radiation.
              </p>
            </div>

            <div className="p-8 rounded-3xl bg-white border border-slate-200 shadow-md space-y-4 relative">
              <span className="text-4xl font-black text-sky-600">02</span>
              <h3 className="text-xl font-bold text-slate-900">10-Sec Handgrip Intake</h3>
              <p className="text-xs sm:text-sm text-slate-600 leading-relaxed">
                A 3-trial digital dynamometer test captures peak physical muscle force, immediately mapped against sex-specific AWGS 2019 cutoff thresholds.
              </p>
            </div>

            <div className="p-8 rounded-3xl bg-white border border-slate-200 shadow-md space-y-4 relative">
              <span className="text-4xl font-black text-sky-600">03</span>
              <h3 className="text-xl font-bold text-slate-900">Multimodal Fusion</h3>
              <p className="text-xs sm:text-sm text-slate-600 leading-relaxed">
                Clinical fusion network correlates imaging features, functional strength, age, and BMI to output instant Sarcopenia and Osteoporosis risk tiers.
              </p>
            </div>
          </div>
        </section>

        {/* 5. COMPARISON TABLE */}
        <section className="px-4 sm:px-8 max-w-7xl mx-auto">
          <div className="text-center space-y-3 mb-12">
            <span className="text-xs font-bold uppercase tracking-wider text-sky-600">
              Comparative Clinical Advantage
            </span>
            <h2 className="text-3xl sm:text-4xl font-extrabold text-slate-900 tracking-tight">
              Why SarcoScan Outperforms Conventional Modalities
            </h2>
          </div>

          <div className="overflow-x-auto rounded-3xl border border-slate-200 bg-white shadow-lg">
            <table className="w-full text-left border-collapse text-xs sm:text-sm">
              <thead>
                <tr className="border-b border-slate-200 bg-slate-50 text-slate-900 font-bold">
                  <th className="p-4 sm:p-5">Clinical Modality</th>
                  <th className="p-4 sm:p-5">Equipment Required</th>
                  <th className="p-4 sm:p-5">Scan / Triage Time</th>
                  <th className="p-4 sm:p-5">Cost per Patient</th>
                  <th className="p-4 sm:p-5">Sarcopenia + Bone Risk</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 text-slate-700">
                <tr className="bg-sky-50/50 font-semibold text-slate-900">
                  <td className="p-4 sm:p-5 flex items-center gap-2">
                    <span className="w-2 h-2 rounded-full bg-sky-600" />
                    <span>SarcoScan AI (Our Solution)</span>
                  </td>
                  <td className="p-4 sm:p-5">Existing Knee X-Ray + Handgrip</td>
                  <td className="p-4 sm:p-5 text-sky-700 font-bold">&lt; 60 Seconds</td>
                  <td className="p-4 sm:p-5 text-sky-700 font-bold">Fractional ($0 Capex)</td>
                  <td className="p-4 sm:p-5 text-emerald-700 font-bold">Dual Instant Risk Staging</td>
                </tr>
                <tr>
                  <td className="p-4 sm:p-5">DEXA (Dual-Energy X-Ray)</td>
                  <td className="p-4 sm:p-5">Dedicated DEXA Machine ($80k+)</td>
                  <td className="p-4 sm:p-5">15 - 20 Minutes</td>
                  <td className="p-4 sm:p-5">$150 - $400</td>
                  <td className="p-4 sm:p-5">Bone Mineral Density Only</td>
                </tr>
                <tr>
                  <td className="p-4 sm:p-5">CT (Computed Tomography)</td>
                  <td className="p-4 sm:p-5">Full CT Scanner ($500k+)</td>
                  <td className="p-4 sm:p-5">10 - 30 Minutes</td>
                  <td className="p-4 sm:p-5">$600 - $1,500</td>
                  <td className="p-4 sm:p-5">High Radiation Exposure</td>
                </tr>
              </tbody>
            </table>
          </div>
        </section>





      </div>
    </div>
  );
}
