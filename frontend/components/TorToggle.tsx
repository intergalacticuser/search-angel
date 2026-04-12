"use client";

interface TorToggleProps {
  enabled: boolean;
  onToggle: (enabled: boolean) => void;
}

export default function TorToggle({ enabled, onToggle }: TorToggleProps) {
  return (
    <button
      onClick={() => onToggle(!enabled)}
      className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs transition-all border ${
        enabled
          ? "bg-purple-500/15 text-purple-400 border-purple-500/30 shadow-lg shadow-purple-500/10"
          : "bg-angel-surface text-angel-muted border-angel-border hover:border-angel-muted/30"
      }`}
      title="Tor Mode: Route all searches through the Tor network for maximum anonymity"
    >
      <svg
        className={`w-4 h-4 ${enabled ? "text-purple-400" : "text-angel-muted"}`}
        viewBox="0 0 24 24"
        fill="currentColor"
      >
        <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 18c-4.42 0-8-3.58-8-8s3.58-8 8-8 8 3.58 8 8-3.58 8-8 8zm0-14c-3.31 0-6 2.69-6 6s2.69 6 6 6 6-2.69 6-6-2.69-6-6-6zm0 10c-2.21 0-4-1.79-4-4s1.79-4 4-4 4 1.79 4 4-1.79 4-4 4zm0-6c-1.1 0-2 .9-2 2s.9 2 2 2 2-.9 2-2-.9-2-2-2z" />
      </svg>
      Tor
      {enabled && (
        <span className="w-1.5 h-1.5 rounded-full bg-purple-400 animate-pulse" />
      )}
    </button>
  );
}
