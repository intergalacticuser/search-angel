"use client";

import { useState } from "react";
import type { SearchResult } from "@/lib/types";
import SourceBadge from "./SourceBadge";

export default function ResultCard({ result }: { result: SearchResult }) {
  const [showExplanation, setShowExplanation] = useState(false);

  return (
    <article className="p-4 rounded-xl border border-angel-border bg-angel-surface/50 hover:border-angel-accent/20 transition-colors">
      {/* URL + Source badge */}
      <div className="flex items-center justify-between gap-2 mb-1">
        <a
          href={result.url}
          target="_blank"
          rel="noopener noreferrer nofollow"
          className="text-xs text-angel-muted truncate hover:text-angel-accent transition-colors"
        >
          {result.url}
        </a>
        <SourceBadge source={result.source} />
      </div>

      {/* Title */}
      <a
        href={result.url}
        target="_blank"
        rel="noopener noreferrer nofollow"
        className="block text-lg font-medium text-angel-accent hover:text-angel-accent-dim transition-colors mb-1"
      >
        {result.title}
      </a>

      {/* Snippet */}
      <p
        className="text-sm text-angel-text/80 leading-relaxed mb-2"
        dangerouslySetInnerHTML={{ __html: result.snippet }}
      />

      {/* Footer: score, evidence, date, explanation toggle */}
      <div className="flex items-center gap-3 text-xs text-angel-muted">
        <span className="font-mono" title="Relevance score">
          Score: {result.score.toFixed(4)}
        </span>

        {result.evidence_count > 0 && (
          <span title="Evidence links">
            {result.evidence_count} evidence link{result.evidence_count > 1 ? "s" : ""}
          </span>
        )}

        {result.published_at && (
          <span>
            {new Date(result.published_at).toLocaleDateString("en-US", {
              year: "numeric",
              month: "short",
              day: "numeric",
            })}
          </span>
        )}

        {result.explanation && (
          <button
            onClick={() => setShowExplanation(!showExplanation)}
            className="text-angel-accent/60 hover:text-angel-accent transition-colors"
          >
            {showExplanation ? "Hide" : "Explain"} score
          </button>
        )}
      </div>

      {/* Score explanation (collapsible) */}
      {showExplanation && result.explanation && (
        <div className="mt-2 p-3 rounded-lg bg-angel-bg border border-angel-border text-xs font-mono">
          {Object.entries(result.explanation).map(([key, value]) => (
            <div key={key} className="flex justify-between py-0.5">
              <span className="text-angel-muted">{key.replace(/_/g, " ")}</span>
              <span className="text-angel-text">{value.toFixed(4)}</span>
            </div>
          ))}
        </div>
      )}
    </article>
  );
}
