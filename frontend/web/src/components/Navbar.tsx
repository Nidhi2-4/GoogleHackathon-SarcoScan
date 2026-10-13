"use client";

import React, { useState } from "react";
import Link from "next/link";
import { ActivityIcon, PhoneIcon, MailIcon } from "@/components/Icons";

export function Navbar() {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  return (
    <header className="sticky top-0 z-40 w-full bg-white/95 backdrop-blur-md border-b border-slate-200 transition-all">

      {/* Main Navigation */}
      <div className="w-full px-6 sm:px-10 lg:px-12">
        <div className="flex items-center justify-between h-16">
          {/* Logo & Brand */}
          <Link href="/" className="flex items-center gap-2.5 group">
            <img
              src="/logo-mark.png"
              alt="SarcoScan Logo"
              className="h-9 w-auto object-contain transition-transform group-hover:scale-105"
            />
            <span className="font-extrabold text-xl tracking-tight text-slate-900">
              Sarco<span className="text-sky-600">Scan</span>
            </span>
          </Link>

          {/* Right Side Navigation Links & Sign Up CTA */}
          <div className="hidden md:flex items-center gap-6 lg:gap-8">
            <Link
              href="/demo"
              className="text-sm font-semibold text-sky-600 hover:text-sky-700 transition-colors"
            >
              Demo
            </Link>
            <Link
              href="/privacy-policy"
              className="text-sm font-medium text-slate-600 hover:text-sky-600 transition-colors"
            >
              Privacy Policy
            </Link>
            <Link
              href="/terms-and-conditions"
              className="text-sm font-medium text-slate-600 hover:text-sky-600 transition-colors"
            >
              Terms & Conditions
            </Link>
            <Link
              href="/about"
              className="text-sm font-medium text-slate-600 hover:text-sky-600 transition-colors"
            >
              About Project
            </Link>
            <Link
              href="/login"
              className="px-5 py-2 rounded-full text-xs font-semibold text-white bg-sky-600 hover:bg-sky-700 shadow-sm shadow-sky-600/20 flex items-center gap-1.5 transition-all"
            >
              <span>Sign up</span>
            </Link>
          </div>

          {/* Mobile Menu Toggle */}
          <div className="md:hidden flex items-center">
            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="p-2 rounded-lg text-slate-700 hover:bg-slate-100 focus:outline-none"
              aria-label="Toggle Navigation Menu"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                {mobileMenuOpen ? (
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
                ) : (
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 6h16M4 12h16M4 18h16" />
                )}
              </svg>
            </button>
          </div>
        </div>
      </div>

      {/* Mobile Menu Drawer */}
      {mobileMenuOpen && (
        <div className="md:hidden bg-white border-b border-slate-200 px-4 pt-2 pb-6 space-y-3">
          <Link
            href="/demo"
            onClick={() => setMobileMenuOpen(false)}
            className="block px-3 py-2 rounded-lg text-base font-semibold text-sky-600 hover:bg-sky-50"
          >
            Demo
          </Link>
          <Link
            href="/privacy-policy"
            onClick={() => setMobileMenuOpen(false)}
            className="block px-3 py-2 rounded-lg text-base font-medium text-slate-800 hover:bg-sky-50"
          >
            Privacy Policy
          </Link>
          <Link
            href="/terms-and-conditions"
            onClick={() => setMobileMenuOpen(false)}
            className="block px-3 py-2 rounded-lg text-base font-medium text-slate-800 hover:bg-sky-50"
          >
            Terms & Conditions
          </Link>
          <Link
            href="/about"
            onClick={() => setMobileMenuOpen(false)}
            className="block px-3 py-2 rounded-lg text-base font-medium text-slate-800 hover:bg-sky-50"
          >
            About Project
          </Link>
          <Link
            href="/login"
            onClick={() => setMobileMenuOpen(false)}
            className="block px-3 py-2 rounded-lg text-base font-semibold text-sky-600 hover:bg-sky-50"
          >
            Sign up
          </Link>
          <div className="pt-3 border-t border-slate-100 space-y-2">
            <a
              href="tel:+18005557272"
              className="flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-semibold text-sky-700 bg-sky-50"
            >
              <PhoneIcon className="w-4 h-4" />
              <span>Call Helpline: +1 (800) 555-7272</span>
            </a>
            <a
              href="mailto:support@sarcoscan.ai"
              className="flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-semibold text-slate-700 bg-slate-50"
            >
              <MailIcon className="w-4 h-4" />
              <span>Email: support@sarcoscan.ai</span>
            </a>
          </div>
        </div>
      )}
    </header>
  );
}
