import React from "react";
import { Skeleton, PatientReportSkeleton } from "@/components/ui/Skeleton";

export default function Loading() {
  return (
    <div className="min-h-screen bg-[#f8fafc] p-6 sm:p-10 space-y-8 max-w-6xl mx-auto">
      {/* Top Banner Skeleton */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 p-6 bg-white rounded-2xl border border-[#e0f2fe] shadow-sm">
        <div className="flex items-center gap-4">
          <Skeleton variant="circular" className="w-14 h-14" />
          <div className="space-y-2">
            <Skeleton variant="text" className="w-56 h-6" />
            <Skeleton variant="text" className="w-72 h-4" />
          </div>
        </div>
        <div className="flex gap-3">
          <Skeleton variant="rectangular" className="w-32 h-10 rounded-xl" />
          <Skeleton variant="rectangular" className="w-36 h-10 rounded-xl" />
        </div>
      </div>

      {/* Main Skeleton Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <div className="lg:col-span-2 space-y-6">
          <PatientReportSkeleton />
          <div className="p-6 bg-white rounded-2xl border border-[#f1f5f9] space-y-4">
            <Skeleton variant="text" className="w-48 h-5" />
            <div className="grid grid-cols-2 gap-4">
              <Skeleton variant="rectangular" className="h-28 rounded-xl" />
              <Skeleton variant="rectangular" className="h-28 rounded-xl" />
            </div>
          </div>
        </div>

        <div className="space-y-6">
          <div className="p-6 bg-white rounded-2xl border border-[#e0f2fe] space-y-4">
            <Skeleton variant="text" className="w-36 h-5" />
            <Skeleton variant="rectangular" className="w-full h-48 rounded-xl" />
            <Skeleton variant="text" className="w-full h-3" />
            <Skeleton variant="text" className="w-4/5 h-3" />
            <Skeleton variant="rectangular" className="w-full h-11 rounded-xl" />
          </div>

          <div className="p-6 bg-white rounded-2xl border border-[#f1f5f9] space-y-4">
            <Skeleton variant="text" className="w-40 h-5" />
            <div className="space-y-2">
              <Skeleton variant="rectangular" className="w-full h-8 rounded" />
              <Skeleton variant="rectangular" className="w-full h-8 rounded" />
              <Skeleton variant="rectangular" className="w-full h-8 rounded" />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
