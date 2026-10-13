import React from "react";

interface SkeletonProps {
  className?: string;
  variant?: "text" | "rectangular" | "circular";
  width?: string | number;
  height?: string | number;
}

export function Skeleton({
  className = "",
  variant = "rectangular",
  width,
  height,
}: SkeletonProps) {
  const baseClasses = "skeleton-shimmer";
  const variantClasses = {
    text: "h-4 rounded",
    rectangular: "rounded-lg",
    circular: "rounded-full",
  };

  const style: React.CSSProperties = {
    width: width,
    height: height,
  };

  return (
    <div
      className={`${baseClasses} ${variantClasses[variant]} ${className}`}
      style={style}
      aria-hidden="true"
    />
  );
}

export function PatientReportSkeleton() {
  return (
    <div className="p-6 rounded-2xl bg-white border border-sky-200 shadow-sm space-y-6">
      <div className="flex items-center justify-between pb-4 border-b border-slate-100">
        <div className="flex items-center gap-4">
          <Skeleton variant="circular" className="w-12 h-12" />
          <div className="space-y-2">
            <Skeleton variant="text" className="w-40 h-5" />
            <Skeleton variant="text" className="w-24 h-4" />
          </div>
        </div>
        <Skeleton variant="rectangular" className="w-28 h-8 rounded-full" />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-3">
          <Skeleton variant="text" className="w-24 h-4" />
          <Skeleton variant="text" className="w-32 h-7" />
          <Skeleton variant="text" className="w-full h-3" />
        </div>
        <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-3">
          <Skeleton variant="text" className="w-28 h-4" />
          <Skeleton variant="text" className="w-36 h-7" />
          <Skeleton variant="text" className="w-full h-3" />
        </div>
        <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-3">
          <Skeleton variant="text" className="w-32 h-4" />
          <Skeleton variant="text" className="w-28 h-7" />
          <Skeleton variant="text" className="w-full h-3" />
        </div>
      </div>

      <div className="space-y-3">
        <Skeleton variant="text" className="w-48 h-4" />
        <Skeleton variant="rectangular" className="w-full h-40 rounded-xl" />
      </div>
    </div>
  );
}
