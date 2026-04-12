"use client";

import { useState, FormEvent } from "react";
import { useRouter } from "next/navigation";
import type { SearchMode } from "@/lib/types";
import GhostMode from "./GhostMode";
import TorToggle from "./TorToggle";

const MODES: { value: SearchMode; label: string; desc: string }[] = [
  { value: "standard", label: "Standard", desc: "Quick hybrid search" },
  { value: "deep", label: "Deep", desc: "Thorough with evidence" },
  { value: "evidence", label: "Evidence", desc: "Source verification" },
  { value: "compare_narratives", label: "Compare", desc: "Multiple perspectives" },
];

export default function SearchBar({
  initialQuery = "",
  initialMode = "standard",
  compact = false,
}: {
  initialQuery?: string;
  initialMode?: SearchMode;
  compact?: boolean;
}) {
  const [query, setQuery] = useState(initialQuery);
  const [mode, setMode] = useState<SearchMode>(initialMode);
  const [ghostMode, setGhostMode] = useState(false);
  const [torMode, setTorMode] = useState(false);
  const router = useRouter();

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;
    const effectiveMode = ghostMode ? "private" : mode;
    const params = new URLSearchParams({ q: query.trim(), mode: effectiveMode });
    if (ghostMode) params.set("ghost", "1");
    if (torMode) params.set("tor", "1");
    router.push(`/search?${params.toString()}`);
  };

  return (
    <form onSubmit={handleSubmit} className="w-full">
      <div className={`relative ${compact ? "max-w-2xl" : "max-w-3xl mx-auto"}`}>
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder={ghostMode ? "Ghost search... (extra private)" : "Search privately..."}
          className={`w-full bg-angel-surface border rounded-2xl
            text-angel-text placeholder:text-angel-muted focus:outline-none
            focus:ring-1 transition-all ${
              ghostMode
                ? "border-angel-accent/40 focus:border-angel-accent focus:ring-angel-accent/30"
                : "border-angel-border focus:border-angel-accent focus:ring-angel-accent/30"
            } ${compact ? "px-5 py-3 text-base" : "px-6 py-4 text-lg"}`}
          autoFocus={!compact}
        />
        <button
          type="submit"
          className={`absolute right-2 bg-angel-accent hover:bg-angel-accent-dim
            text-angel-bg font-medium rounded-xl transition-colors
            ${compact ? "top-1.5 px-4 py-1.5 text-sm" : "top-2 px-5 py-2 text-base"}`}
        >
          Search
        </button>
      </div>

      {/* Mode selector + Ghost mode */}
      <div className={`flex items-center gap-2 mt-3 ${compact ? "" : "justify-center"} flex-wrap`}>
        {MODES.map((m) => (
          <button
            key={m.value}
            type="button"
            onClick={() => setMode(m.value)}
            className={`px-3 py-1.5 rounded-lg text-sm transition-all ${
              mode === m.value && !ghostMode
                ? "bg-angel-accent/15 text-angel-accent border border-angel-accent/30"
                : "bg-angel-surface text-angel-muted border border-angel-border hover:border-angel-muted/30"
            }`}
            title={m.desc}
          >
            {m.label}
          </button>
        ))}

        <div className="w-px h-5 bg-angel-border mx-1" />

        <GhostMode enabled={ghostMode} onToggle={setGhostMode} />
        <TorToggle enabled={torMode} onToggle={setTorMode} />
      </div>

      {/* Privacy notice under search bar */}
      {!compact && (
        <p className="text-center text-xs text-angel-muted/50 mt-3">
          This search is not recorded. Your IP is hashed and discarded.
        </p>
      )}
    </form>
  );
}
