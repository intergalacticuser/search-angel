"use client";

import Link from "next/link";
import PrivacyShield from "./PrivacyShield";

export default function Header() {
  return (
    <header className="border-b border-angel-border bg-angel-surface/80 backdrop-blur-sm sticky top-0 z-50">
      <div className="max-w-6xl mx-auto px-4 h-14 flex items-center justify-between">
        <Link href="/" className="flex items-center gap-2">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img
            src="/logo.png"
            alt="Search Angel"
            width={40}
            height={27}
            className="object-contain"
          />
          <span className="font-semibold text-angel-text hidden sm:inline">Search Angel</span>
        </Link>
        <div className="flex items-center gap-4">
          <PrivacyShield />
          <Link
            href="/privacy"
            className="text-xs text-angel-muted hover:text-angel-accent transition-colors"
          >
            Privacy
          </Link>
        </div>
      </div>
    </header>
  );
}
