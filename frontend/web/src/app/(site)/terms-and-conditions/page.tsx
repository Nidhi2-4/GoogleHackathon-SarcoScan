import React from "react";
import Link from "next/link";
import { AlertTriangleIcon, FileTextIcon, PhoneIcon, MailIcon, ShieldCheckIcon } from "@/components/Icons";

export const metadata = {
  title: "Terms and Conditions · SarcoScan AI Screening Platform",
  description: "Terms and conditions of use for SarcoScan research and pilot clinical screening software.",
};

export default function TermsAndConditionsPage() {
  return (
    <div className="py-12 px-4 sm:px-8 max-w-5xl mx-auto space-y-12">
      {/* Header section */}
      <div className="p-8 sm:p-12 rounded-3xl bg-white border border-slate-200 shadow-xl shadow-sky-900/5 space-y-4">
        <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-sky-50 text-sky-700 text-xs font-semibold border border-sky-200">
          <FileTextIcon className="w-4 h-4" />
          <span>Research & Pilot Terms of Service</span>
        </div>
        <h1 className="text-3xl sm:text-4xl font-extrabold tracking-tight text-slate-900">
          SarcoScan Terms and Conditions
        </h1>
        <p className="text-sm sm:text-base text-slate-500 leading-relaxed">
          Last Updated: October 2026 · SarcoScan Research Consortium
        </p>
      </div>

      {/* Critical Medical Disclaimer Warning Box */}
      <div className="p-6 sm:p-8 rounded-3xl bg-amber-50/50 border-2 border-amber-200 space-y-3">
        <div className="flex items-center gap-2.5 text-amber-900 font-bold text-lg">
          <AlertTriangleIcon className="w-6 h-6 text-amber-600" />
          <h2>Mandatory Clinical Research Disclaimer</h2>
        </div>
        <p className="text-sm text-slate-800 leading-relaxed font-medium">
          SarcoScan is a software prototype developed for clinical research demonstration and validation. It is <strong>NOT</strong> an FDA/CE-cleared diagnostic medical device and must <strong>NOT</strong> be used as a standalone diagnostic determination or treatment prescription.
        </p>
        <p className="text-xs text-slate-600 leading-relaxed">
          All algorithmic risk tiers (Sarcopenia staging and Osteoporosis probability) are intended solely as auxiliary screening prompts to assist licensed healthcare professionals in triage and referral decisions.
        </p>
      </div>

      {/* Legal terms breakdown */}
      <div className="bg-white rounded-3xl border border-slate-200 shadow-sm p-8 sm:p-12 space-y-10 text-sm text-slate-700 leading-relaxed">
        <section className="space-y-3">
          <h2 className="text-xl font-bold text-slate-900 border-b border-slate-100 pb-2">
            1. Acceptance of Terms
          </h2>
          <p>
            By accessing or operating the SarcoScan web portal, technician dynamometer client, or automated inference pipeline, medical institutions, technicians, and clinicians agree to abide by these terms of use.
          </p>
        </section>

        <section className="space-y-3">
          <h2 className="text-xl font-bold text-slate-900 border-b border-slate-100 pb-2">
            2. Intended User Roles & Obligations
          </h2>
          <p>The platform provides distinct interfaces for verified operational roles:</p>
          <ul className="list-disc pl-5 space-y-1 text-slate-600">
            <li><strong>Radiology Technicians & Nurses:</strong> Responsible for verifying patient positioning during knee AP X-ray acquisition and ensuring proper dynamometer calibration.</li>
            <li><strong>Orthopedic & Geriatric Clinicians:</strong> Responsible for reviewing AI-generated segmentations, evaluating confidence intervals, and applying independent clinical judgment before making diagnostic referrals.</li>
            <li><strong>Hospital Administrators:</strong> Responsible for local server security, user access revocation, and backup integrity.</li>
          </ul>
        </section>

        <section className="space-y-3">
          <h2 className="text-xl font-bold text-slate-900 border-b border-slate-100 pb-2">
            3. Limitation of Liability
          </h2>
          <p>
            The developers and affiliated clinical researchers assume no liability for patient treatment decisions, misdiagnoses, delayed interventions, or inaccuracies arising from distorted radiograph inputs or patient dynamometer non-compliance.
          </p>
        </section>

        <section className="space-y-3">
          <h2 className="text-xl font-bold text-slate-900 border-b border-slate-100 pb-2">
            4. Open Research & Intellectual Property
          </h2>
          <p>
            The underlying deep learning fusion architecture, soft-tissue-to-bone ratio extraction algorithms, and UX design are provided under open academic research licensing for participating pilot hospitals.
          </p>
        </section>

        <section className="space-y-4 pt-4 border-t border-slate-100">
          <h2 className="text-xl font-bold text-slate-900">
            5. Inquiries & Legal Governance
          </h2>
          <p className="text-slate-600">
            For institutional licensing, trial agreements, or questions about these terms:
          </p>
          <div className="flex flex-wrap items-center gap-4 pt-2">
            <a
              href="mailto:legal@sarcoscan.ai"
              className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl bg-sky-600 hover:bg-sky-700 text-white font-semibold transition-colors shadow-sm shadow-sky-600/20"
            >
              <MailIcon className="w-4 h-4" />
              <span>legal@sarcoscan.ai</span>
            </a>
            <a
              href="tel:+18005557272"
              className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl bg-slate-50 hover:bg-slate-100 border border-slate-200 text-slate-800 font-semibold transition-colors shadow-sm"
            >
              <PhoneIcon className="w-4 h-4 text-sky-600" />
              <span>+1 (800) 555-7272</span>
            </a>
          </div>
        </section>
      </div>
    </div>
  );
}
