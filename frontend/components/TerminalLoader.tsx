"use client";

import { useState, useEffect } from "react";

const BOOT_LINES = [
  { text: "> ATLAS SECURE PROTOCOL v2.0", delay: 100 },
  { text: "> INITIALIZING ENCRYPTED CHANNEL...", delay: 200 },
  { text: "  [################] CONNECTED", delay: 400, color: "green" },
  { text: "> VERIFYING PRIVACY SHIELDS...", delay: 200 },
  { text: "  COOKIES: BLOCKED", delay: 150, color: "green" },
  { text: "  TRACKERS: NEUTRALIZED", delay: 150, color: "green" },
  { text: "  IP: ANONYMIZED", delay: 150, color: "green" },
  { text: "> LOADING SEARCH ANGEL ENGINE...", delay: 300 },
  { text: "  BM25 RETRIEVER: ONLINE", delay: 100, color: "cyan" },
  { text: "  VECTOR ENGINE: ONLINE", delay: 100, color: "cyan" },
  { text: "  SEARXNG META-SEARCH: ONLINE", delay: 100, color: "cyan" },
  { text: "  EVIDENCE RANKER: ONLINE", delay: 100, color: "cyan" },
  { text: "> ALL SYSTEMS OPERATIONAL", delay: 200, color: "green" },
  { text: "> ENTERING SEARCH ANGEL...", delay: 400, color: "cyan" },
];

export default function TerminalLoader({ onComplete }: { onComplete: () => void }) {
  const [lines, setLines] = useState<Array<{ text: string; color?: string }>>([]);
  const [done, setDone] = useState(false);
  const [fadeOut, setFadeOut] = useState(false);

  useEffect(() => {
    let idx = 0;
    let totalDelay = 0;

    BOOT_LINES.forEach((line, i) => {
      totalDelay += line.delay;
      setTimeout(() => {
        setLines((prev) => [...prev, { text: line.text, color: line.color }]);
      }, totalDelay);
    });

    // Fade out after all lines
    setTimeout(() => setFadeOut(true), totalDelay + 500);
    setTimeout(() => {
      setDone(true);
      onComplete();
    }, totalDelay + 1000);
  }, [onComplete]);

  if (done) return null;

  return (
    <div
      className={`fixed inset-0 z-[9999] bg-black flex items-center justify-center transition-opacity duration-500 ${
        fadeOut ? "opacity-0" : "opacity-100"
      }`}
    >
      {/* Matrix-style background particles */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        {Array.from({ length: 30 }).map((_, i) => (
          <div
            key={i}
            className="absolute text-green-500/10 text-xs font-mono animate-pulse"
            style={{
              left: `${Math.random() * 100}%`,
              top: `${Math.random() * 100}%`,
              animationDelay: `${Math.random() * 2}s`,
              animationDuration: `${1 + Math.random() * 3}s`,
            }}
          >
            {Math.random() > 0.5 ? "1" : "0"}
          </div>
        ))}
      </div>

      {/* Terminal window */}
      <div className="relative w-full max-w-2xl mx-4">
        {/* Terminal header */}
        <div className="flex items-center gap-2 px-4 py-2 bg-gray-900 rounded-t-xl border border-gray-700 border-b-0">
          <div className="w-3 h-3 rounded-full bg-red-500/80" />
          <div className="w-3 h-3 rounded-full bg-yellow-500/80" />
          <div className="w-3 h-3 rounded-full bg-green-500/80" />
          <span className="ml-4 text-xs text-gray-500 font-mono">
            atlas-secure-protocol
          </span>
        </div>

        {/* Terminal body */}
        <div className="bg-gray-950 border border-gray-700 rounded-b-xl p-6 font-mono text-sm min-h-[300px] max-h-[400px] overflow-hidden">
          {lines.map((line, i) => (
            <div
              key={i}
              className={`mb-1 ${
                line.color === "green"
                  ? "text-green-400"
                  : line.color === "cyan"
                    ? "text-cyan-400"
                    : "text-gray-300"
              }`}
              style={{
                animation: "fadeIn 0.1s ease-in",
              }}
            >
              {line.text}
            </div>
          ))}
          {/* Blinking cursor */}
          {!fadeOut && (
            <span className="inline-block w-2 h-4 bg-green-400 animate-pulse" />
          )}
        </div>
      </div>

      <style jsx>{`
        @keyframes fadeIn {
          from { opacity: 0; transform: translateY(4px); }
          to { opacity: 1; transform: translateY(0); }
        }
      `}</style>
    </div>
  );
}
