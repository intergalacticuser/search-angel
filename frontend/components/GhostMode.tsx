"use client";

interface GhostModeProps {
  enabled: boolean;
  onToggle: (enabled: boolean) => void;
}

export default function GhostMode({ enabled, onToggle }: GhostModeProps) {
  return (
    <button
      onClick={() => onToggle(!enabled)}
      className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs transition-all border ${
        enabled
          ? "bg-angel-accent/10 text-angel-accent border-angel-accent/30 shadow-lg shadow-angel-accent/10"
          : "bg-angel-surface text-angel-muted border-angel-border hover:border-angel-muted/30"
      }`}
      title="Ghost Mode: Extra privacy - no caching, no referrer, forces private mode"
    >
      <span className={`text-base ${enabled ? "animate-pulse" : ""}`}>
        {enabled ? "\uD83D\uDC7B" : "\uD83D\uDC7B"}
      </span>
      Ghost
    </button>
  );
}
