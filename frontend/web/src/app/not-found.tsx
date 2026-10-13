import React from "react";
import Link from "next/link";
import { ActivityIcon, PhoneIcon, MailIcon, ArrowRightIcon, AlertTriangleIcon } from "@/components/Icons";

export default function NotFound() {
  return (
    <div className="min-h-[75vh] flex items-center justify-center p-6 sm:p-12">
      <div className="max-w-2xl w-full bg-white rounded-3xl border border-slate-200 shadow-xl shadow-sky-900/5 p-8 sm:p-12 text-center space-y-8">
        {/* Visual Badge */}
        <div className="inline-flex items-center justify-center w-20 h-20 rounded-2xl bg-sky-50 text-sky-600 border-2 border-sky-200 shadow-inner mx-auto">
          <span className="text-3xl font-extrabold">404</span>
        </div>

        {/* Heading and details */}
        <div className="space-y-3">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-amber-50 border border-amber-200 text-xs font-semibold text-amber-800">
            <AlertTriangleIcon className="w-4 h-4 text-amber-600" />
            <span>Diagnostic Path Not Found</span>
          </div>
          <h1 className="text-3xl sm:text-4xl font-bold tracking-tight text-slate-900">
            Page or Clinical Record Missing
          </h1>
          <p className="text-sm sm:text-base text-slate-600 max-w-lg mx-auto leading-relaxed">
            The screening module, patient record, or documentation endpoint you are looking for has moved, expired, or does not exist on this on-premise SarcoScan instance.
          </p>
        </div>

        {/* Quick Navigation Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-left pt-2">
          <Link
            href="/"
            className="p-4 rounded-xl bg-slate-50 hover:bg-sky-50/50 border border-slate-200 hover:border-sky-300 transition-all group"
          >
            <div className="flex items-center justify-between mb-1">
              <span className="font-semibold text-sm text-slate-900 group-hover:text-sky-600">
                Screening Suite
              </span>
              <ArrowRightIcon className="w-4 h-4 text-slate-400 group-hover:translate-x-1 group-hover:text-sky-600 transition-all" />
            </div>
            <p className="text-xs text-slate-500">Run AI knee AP X-ray + grip test fusion model</p>
          </Link>

          <Link
            href="/about"
            className="p-4 rounded-xl bg-slate-50 hover:bg-sky-50/50 border border-slate-200 hover:border-sky-300 transition-all group"
          >
            <div className="flex items-center justify-between mb-1">
              <span className="font-semibold text-sm text-slate-900 group-hover:text-sky-600">
                About SarcoScan
              </span>
              <ArrowRightIcon className="w-4 h-4 text-slate-400 group-hover:translate-x-1 group-hover:text-sky-600 transition-all" />
            </div>
            <p className="text-xs text-slate-500">Learn about SarcoScan and the clinical mission</p>
          </Link>
        </div>

        {/* Need assistance helpline */}
        <div className="pt-6 border-t border-slate-100 flex flex-col sm:flex-row items-center justify-between gap-4 text-xs text-slate-600">
          <div className="flex items-center gap-2">
            <span>Need immediate hospital support?</span>
          </div>
          <div className="flex items-center gap-3">
            <a
              href="tel:+18005557272"
              className="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg bg-sky-50 hover:bg-sky-100 text-sky-700 font-medium transition-colors border border-sky-200"
            >
              <PhoneIcon className="w-3.5 h-3.5" />
              <span>+1 (800) 555-7272</span>
            </a>
            <a
              href="mailto:support@sarcoscan.ai"
              className="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-800 font-medium transition-colors"
            >
              <MailIcon className="w-3.5 h-3.5" />
              <span>support@sarcoscan.ai</span>
            </a>
          </div>
        </div>
      </div>
    </div>
  );
}
