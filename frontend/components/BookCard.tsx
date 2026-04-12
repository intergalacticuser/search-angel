import type { SearchResult } from "@/lib/types";

export default function BookCard({ result }: { result: SearchResult }) {
  const isbn = (result.media_metadata?.isbn as string[]) || [];
  const publisher = result.media_metadata?.publisher as string | undefined;

  return (
    <a
      href={result.url}
      target="_blank"
      rel="noopener noreferrer nofollow"
      className="flex gap-4 p-4 rounded-xl border border-angel-border bg-angel-surface/50 hover:border-angel-accent/20 transition-colors"
    >
      {/* Book cover */}
      <div className="w-20 h-28 shrink-0 rounded-lg overflow-hidden bg-angel-bg border border-angel-border flex items-center justify-center">
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
          <svg className="w-8 h-8 text-angel-muted" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
          </svg>
        )}
      </div>

      <div className="flex-1 min-w-0">
        <span className="text-[10px] font-mono text-amber-400 bg-amber-400/10 px-1.5 py-0.5 rounded">
          BOOK
        </span>
        <h3 className="text-base font-medium text-angel-text mt-1 line-clamp-2">
          {result.title}
        </h3>
        {result.author && (
          <p className="text-sm text-angel-accent mt-0.5">by {result.author}</p>
        )}
        <p className="text-xs text-angel-muted line-clamp-2 mt-1">{result.snippet}</p>
        <div className="flex items-center gap-3 mt-2 text-[10px] text-angel-muted">
          <span>{result.source.domain}</span>
          {publisher && <span>{publisher}</span>}
          {isbn.length > 0 && <span className="font-mono">ISBN: {isbn[0]}</span>}
        </div>
      </div>
    </a>
  );
}
