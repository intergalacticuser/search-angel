"use client";

import type { SearchResult } from "@/lib/types";

export default function ImageGrid({ results }: { results: SearchResult[] }) {
  if (results.length === 0) {
    return (
      <div className="text-center py-16 text-angel-muted">
        No images found
      </div>
    );
  }

  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-3">
      {results.map((result) => (
        <a
          key={result.id}
          href={result.url}
          target="_blank"
          rel="noopener noreferrer nofollow"
          className="group relative rounded-xl overflow-hidden border border-angel-border bg-angel-surface/30 hover:border-angel-accent/30 transition-all"
        >
          <div className="aspect-square bg-angel-bg flex items-center justify-center overflow-hidden">
            {result.img_src || result.thumbnail ? (
              /* eslint-disable-next-line @next/next/no-img-element */
              <img
                src={result.img_src || result.thumbnail || ""}
                alt={result.title}
                className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                loading="lazy"
                onError={(e) => {
                  (e.target as HTMLImageElement).style.display = "none";
                }}
              />
            ) : (
              <div className="text-angel-muted text-xs p-2 text-center">{result.title.slice(0, 50)}</div>
            )}
          </div>
          {/* Overlay on hover */}
          <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity flex flex-col justify-end p-2">
            <p className="text-white text-xs font-medium line-clamp-2">{result.title}</p>
            <p className="text-white/60 text-[10px] mt-0.5">{result.source.domain}</p>
          </div>
        </a>
      ))}
    </div>
  );
}
