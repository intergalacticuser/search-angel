"use client";

import type { SearchResult } from "@/lib/types";

export default function VideoCard({ result }: { result: SearchResult }) {
  const duration = result.media_metadata?.duration as string | undefined;

  return (
    <a
      href={result.url}
      target="_blank"
      rel="noopener noreferrer nofollow"
      className="flex gap-4 p-3 rounded-xl border border-angel-border bg-angel-surface/50 hover:border-angel-accent/20 transition-colors"
    >
      {/* Thumbnail */}
      <div className="relative w-48 h-28 shrink-0 rounded-lg overflow-hidden bg-angel-bg">
        {result.thumbnail ? (
          /* eslint-disable-next-line @next/next/no-img-element */
          <img
            src={result.thumbnail}
            alt={result.title}
            className="w-full h-full object-cover"
            loading="lazy"
            onError={(e) => {
              (e.target as HTMLImageElement).style.display = "none";
            }}
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center text-angel-muted">
            <svg className="w-10 h-10" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM9.555 7.168A1 1 0 008 8v4a1 1 0 001.555.832l3-2a1 1 0 000-1.664l-3-2z" clipRule="evenodd" />
            </svg>
          </div>
        )}
        {/* Duration badge */}
        {duration && (
          <span className="absolute bottom-1 right-1 bg-black/80 text-white text-[10px] font-mono px-1.5 py-0.5 rounded">
            {duration}
          </span>
        )}
        {/* Play icon overlay */}
        <div className="absolute inset-0 flex items-center justify-center opacity-0 hover:opacity-100 transition-opacity bg-black/30">
          <svg className="w-8 h-8 text-white" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM9.555 7.168A1 1 0 008 8v4a1 1 0 001.555.832l3-2a1 1 0 000-1.664l-3-2z" clipRule="evenodd" />
          </svg>
        </div>
      </div>

      {/* Info */}
      <div className="flex-1 min-w-0">
        <h3 className="text-sm font-medium text-angel-accent line-clamp-2 mb-1">
          {result.title}
        </h3>
        <p className="text-xs text-angel-muted line-clamp-2 mb-2">{result.snippet}</p>
        <div className="flex items-center gap-2 text-[10px] text-angel-muted">
          <span>{result.source.domain}</span>
          {result.author && (
            <>
              <span className="w-1 h-1 rounded-full bg-angel-muted/30" />
              <span>{result.author}</span>
            </>
          )}
          {result.published_at && (
            <>
              <span className="w-1 h-1 rounded-full bg-angel-muted/30" />
              <span>{new Date(result.published_at).toLocaleDateString()}</span>
            </>
          )}
        </div>
      </div>
    </a>
  );
}
