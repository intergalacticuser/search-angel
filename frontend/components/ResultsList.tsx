import type { SearchResult } from "@/lib/types";
import ResultCard from "./ResultCard";

export default function ResultsList({ results }: { results: SearchResult[] }) {
  if (results.length === 0) {
    return (
      <div className="text-center py-16">
        <p className="text-angel-muted text-lg">No results found</p>
        <p className="text-angel-muted/60 text-sm mt-1">Try different keywords or broaden your filters</p>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {results.map((result) => (
        <ResultCard key={result.id} result={result} />
      ))}
    </div>
  );
}
