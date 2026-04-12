import type { SearchResult } from "@/lib/types";
import SourceBadge from "./SourceBadge";

export default function NewsCard({ result }: { result: SearchResult }) {
  return (
    <a
      href={result.url}
      target="_blank"
      rel="noopener noreferrer nofollow"
      className="flex gap-4 p-4 rounded-xl border border-angel-border bg-angel-surface/50 hover:border-angel-accent/20 transition-colors"
    >
      {/* Thumbnail */}
      {result.thumbnail && (
        <div className="w-32 h-24 shrink-0 rounded-lg overflow-hidden bg-angel-bg">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img
            src={result.thumbnail}
            alt=""
            className="w-full h-full object-cover"
            loading="lazy"
            onError={(e) => {
              (e.target as HTMLImageElement).parentElement!.style.display = "none";
            }}
          />
        </div>
      )}

      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 mb-1">
          <span className="text-[10px] font-mono text-angel-accent bg-angel-accent/10 px-1.5 py-0.5 rounded">
            NEWS
          </span>
          <SourceBadge source={result.source} />
        </div>
        <h3 className="text-base font-medium text-angel-text line-clamp-2 mb-1">
          {result.title}
        </h3>
        <p className="text-sm text-angel-muted line-clamp-2 mb-2">{result.snippet}</p>
        <div className="flex items-center gap-2 text-xs text-angel-muted">
          {result.published_at && (
            <span>
              {new Date(result.published_at).toLocaleDateString("en-US", {
                year: "numeric",
                month: "short",
                day: "numeric",
              })}
            </span>
          )}
          {result.author && <span>by {result.author}</span>}
        </div>
      </div>
    </a>
  );
}
