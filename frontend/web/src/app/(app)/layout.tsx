"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect } from "react";
import { ModelStatus } from "@/components/app";
import { signOut, useStore } from "@/lib/store";

const NAV = [
  ["/dashboard", "Dashboard"],
  ["/patients", "Patients"],
  ["/studies", "Studies Inbox"],
  ["/reports", "Reports"],
  ["/analytics", "Analytics"],
  ["/admin", "Admin"],
  ["/settings", "Settings"],
];

export default function AppLayout({ children }: { children: React.ReactNode }) {
  const { ready, user } = useStore();
  const path = usePathname();
  const router = useRouter();

  useEffect(() => {
    if (ready && !user) router.replace("/login");
  }, [ready, user, router]);

  if (!user) return null;

  return (
    <div className="flex flex-1 flex-col md:flex-row">
      <nav className="no-print flex shrink-0 gap-1 overflow-x-auto border-[#e2e8f0] bg-white p-3 max-md:border-b md:w-52 md:flex-col md:border-r">
        <Link href="/dashboard" className="px-3 py-2 text-lg font-bold">
          SarcoScan
        </Link>
        {NAV.filter(([href]) => href !== "/admin" || user.role === "admin").map(([href, label]) => (
          <Link
            key={href}
            href={href}
            aria-current={path.startsWith(href) ? "page" : undefined}
            className="rounded-lg px-3 py-2 text-sm font-medium whitespace-nowrap hover:bg-[#e0f2fe]/50 aria-[current]:bg-[#e0f2fe]"
          >
            {label}
          </Link>
        ))}
        <p className="px-3 py-2 text-xs text-[#64748b] md:mt-auto">
          {user.name}
          <br />
          <span className="capitalize">{user.role}</span>
        </p>
        <div className="px-3 pb-2">
          <ModelStatus />
        </div>
        <button className="btn-ghost" onClick={signOut}>
          Log out
        </button>
      </nav>
      <main className="mx-auto w-full max-w-6xl flex-1 space-y-6 p-4 md:p-8">{children}</main>
    </div>
  );
}
