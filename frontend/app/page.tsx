"use client";

import { useState, useCallback } from "react";
import SearchBar from "@/components/SearchBar";
import PrivacyNotice from "@/components/PrivacyNotice";
import TerminalLoader from "@/components/TerminalLoader";
import PhantomMode from "@/components/PhantomMode";
import Link from "next/link";

export default function Home() {
  const [showLoader, setShowLoader] = useState(true);
  const handleLoaderComplete = useCallback(() => setShowLoader(false), []);

  return (
    <>
      {showLoader && <TerminalLoader onComplete={handleLoaderComplete} />}
    <main className="min-h-screen flex flex-col items-center justify-center px-4">
      {/* Logo */}
      <div className="mb-6 text-center">
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img
          src="/logo.png"
          alt="Search Angel"
          width={280}
          height={187}
          className="mx-auto mb-2 drop-shadow-2xl"
        />
        <p className="text-angel-muted text-lg mt-2">Privacy-first deep search</p>
      </div>

      {/* Search Bar */}
      <div className="w-full max-w-3xl">
        <SearchBar />
        <PhantomMode />
      </div>

      {/* Privacy Manifesto */}
      <div className="mt-10 max-w-3xl w-full">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          {[
            { icon: "\uD83D\uDD12", title: "Zero Tracking", desc: "No cookies, no fingerprinting, no profiling" },
            { icon: "\uD83D\uDC7B", title: "Ghost Mode", desc: "Extra privacy with ephemeral sessions" },
            { icon: "\uD83C\uDF10", title: "Web-Wide Search", desc: "70+ engines via self-hosted SearXNG" },
            { icon: "\uD83D\uDEE1\uFE0F", title: "Evidence-Based", desc: "Source credibility scoring + fact verification" },
          ].map((f) => (
            <div
              key={f.title}
              className="p-4 rounded-xl border border-angel-border bg-angel-surface/30 text-center hover:border-angel-accent/20 transition-colors"
            >
              <div className="text-2xl mb-2">{f.icon}</div>
              <h3 className="text-sm font-medium text-angel-text mb-1">{f.title}</h3>
              <p className="text-xs text-angel-muted">{f.desc}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Privacy link */}
      <div className="mt-8">
        <Link
          href="/privacy"
          className="text-sm text-angel-accent/70 hover:text-angel-accent transition-colors flex items-center gap-1"
        >
          <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M10 1a1 1 0 011 1v1.323l3.954 1.582 1.599-.8a1 1 0 01.894 1.79l-1.233.616c.078.348.118.71.118 1.082 0 3.17-1.894 6.032-4.834 7.526a1 1 0 01-.996 0C7.562 13.625 5.668 10.763 5.668 7.593c0-.372.04-.734.118-1.082L4.553 5.895a1 1 0 01.894-1.789l1.599.8L11 3.323V2a1 1 0 01-1-1z" clipRule="evenodd" />
          </svg>
          How we protect your privacy
        </Link>
      </div>

      <PrivacyNotice />
    </main>
    </>
  );
}
