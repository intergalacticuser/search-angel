"use client";

import { useSearchParams } from "next/navigation";
import { useEffect, useState, useCallback, Suspense } from "react";
import Header from "@/components/Header";
import SearchBar from "@/components/SearchBar";
import ResultsList from "@/components/ResultsList";
import SummaryPanel from "@/components/SummaryPanel";
import PrivacyNotice from "@/components/PrivacyNotice";
import CategoryTabs from "@/components/CategoryTabs";
import ImageGrid from "@/components/ImageGrid";
import VideoCard from "@/components/VideoCard";
import NewsCard from "@/components/NewsCard";
import BookCard from "@/components/BookCard";
import { api } from "@/lib/api";
import type {
  SearchMode,
  SearchCategory,
  SearchResponse,
  CategorySearchResponse,
  SearchResult,
} from "@/lib/types";

function SearchContent() {
  const searchParams = useSearchParams();
  const query = searchParams.get("q") || "";
  const mode = (searchParams.get("mode") || "standard") as SearchMode;
  const initialCategory = (searchParams.get("cat") || "general") as SearchCategory;
  const torEnabled = searchParams.get("tor") === "1";

  const [category, setCategory] = useState<SearchCategory>(initialCategory);
  const [webResponse, setWebResponse] = useState<SearchResponse | null>(null);
  const [catResponse, setCatResponse] = useState<CategorySearchResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const doSearch = useCallback(async () => {
    if (!query) return;
    setLoading(true);
    setError(null);

    try {
      if (category === "general") {
        const res = await api.search({
          query,
          mode,
          include_summary: mode === "deep" || mode === "evidence",
          limit: 20,
          tor_mode: torEnabled,
        });
        setWebResponse(res);
        setCatResponse(null);
      } else {
        const res = await api.categorySearch(query, category, 30, 0, torEnabled);
        setCatResponse(res);
        setWebResponse(null);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Search failed");
    } finally {
      setLoading(false);
    }
  }, [query, mode, category, torEnabled]);

  useEffect(() => {
    doSearch();
  }, [doSearch]);

  const results: SearchResult[] =
    webResponse?.results || catResponse?.results || [];
  const total = webResponse?.total || catResponse?.total || 0;
  const timingMs = webResponse?.timing_ms || catResponse?.timing_ms || 0;

  return (
    <div className="min-h-screen flex flex-col">
      <Header />

      {/* Search bar */}
      <div className="border-b border-angel-border bg-angel-surface/30 px-4 py-3">
        <div className="max-w-6xl mx-auto">
          <SearchBar initialQuery={query} initialMode={mode} compact />
        </div>
      </div>

      {/* Tor indicator */}
      {torEnabled && (
        <div className="bg-purple-500/10 border-b border-purple-500/20 px-4 py-1.5">
          <div className="max-w-6xl mx-auto flex items-center gap-2 text-xs text-purple-400">
            <span className="w-2 h-2 rounded-full bg-purple-400 animate-pulse" />
            Tor Mode Active - All searches routed through the Tor network
          </div>
        </div>
      )}

      {/* Category tabs */}
      <div className="border-b border-angel-border bg-angel-surface/10 px-4 py-2">
        <div className="max-w-6xl mx-auto">
          <CategoryTabs active={category} onChange={setCategory} />
        </div>
      </div>

      {/* Main content */}
      <main className="flex-1 max-w-6xl mx-auto w-full px-4 py-6">
        {/* Metadata bar */}
        {!loading && total > 0 && (
          <div className="flex items-center gap-4 mb-4 text-xs text-angel-muted">
            <span>
              {total} result{total !== 1 ? "s" : ""}
            </span>
            <span className="font-mono">{timingMs.toFixed(0)}ms</span>
            {webResponse?.query_metadata && (
              <>
                <span>Intent: {webResponse.query_metadata.intent}</span>
                {webResponse.query_metadata.expanded_terms.length > 0 && (
                  <span>
                    +{webResponse.query_metadata.expanded_terms.length} expanded
                  </span>
                )}
              </>
            )}
          </div>
        )}

        {/* AI Summary (general mode only) */}
        {webResponse?.summary && (
          <div className="mb-6">
            <SummaryPanel summary={webResponse.summary} />
          </div>
        )}

        {/* Loading skeleton */}
        {loading && (
          <div className="space-y-3">
            {[1, 2, 3, 4].map((i) => (
              <div
                key={i}
                className="p-4 rounded-xl border border-angel-border bg-angel-surface/30 animate-pulse"
              >
                <div className="h-4 bg-angel-border rounded w-3/4 mb-2" />
                <div className="h-3 bg-angel-border rounded w-1/2 mb-3" />
                <div className="h-3 bg-angel-border rounded w-full" />
              </div>
            ))}
          </div>
        )}

        {/* Error */}
        {error && (
          <div className="p-4 rounded-xl border border-angel-red/30 bg-angel-red/5 text-angel-red text-sm">
            {error}
          </div>
        )}

        {/* Results by category */}
        {!loading && results.length > 0 && (
          <>
            {category === "general" && <ResultsList results={results} />}

            {category === "images" && <ImageGrid results={results} />}

            {category === "videos" && (
              <div className="space-y-3">
                {results.map((r) => (
                  <VideoCard key={r.id} result={r} />
                ))}
              </div>
            )}

            {category === "news" && (
              <div className="space-y-3">
                {results.map((r) => (
                  <NewsCard key={r.id} result={r} />
                ))}
              </div>
            )}

            {(category === "books" || category === "science") && (
              <div className="space-y-3">
                {results.map((r) => (
                  <BookCard key={r.id} result={r} />
                ))}
              </div>
            )}

            {(category === "music" || category === "files") && (
              <ResultsList results={results} />
            )}
          </>
        )}

        {/* No results */}
        {!loading && !error && results.length === 0 && query && (
          <div className="text-center py-16">
            <p className="text-angel-muted text-lg">No {category} results found</p>
            <p className="text-angel-muted/60 text-sm mt-1">
              Try different keywords or another category
            </p>
          </div>
        )}

        {/* No query */}
        {!query && (
          <div className="text-center py-16 text-angel-muted">
            Enter a search query above
          </div>
        )}
      </main>

      <PrivacyNotice />
    </div>
  );
}

export default function SearchPage() {
  return (
    <Suspense
      fallback={
        <div className="min-h-screen flex items-center justify-center text-angel-muted">
          Loading...
        </div>
      }
    >
      <SearchContent />
    </Suspense>
  );
}
