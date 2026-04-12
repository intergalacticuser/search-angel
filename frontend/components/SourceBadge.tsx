import type { SourceInfo } from "@/lib/types";

function credibilityColor(score: number): string {
  if (score >= 0.8) return "bg-angel-green/15 text-angel-green border-angel-green/30";
  if (score >= 0.5) return "bg-amber-500/15 text-amber-400 border-amber-500/30";
  return "bg-angel-red/15 text-angel-red border-angel-red/30";
}

function biasColor(bias: string): string {
  const colors: Record<string, string> = {
    left: "text-blue-400",
    center_left: "text-sky-400",
    center: "text-angel-muted",
    center_right: "text-orange-400",
    right: "text-red-400",
    unknown: "text-angel-muted",
  };
  return colors[bias] || "text-angel-muted";
}

function biasLabel(bias: string): string {
  const labels: Record<string, string> = {
    left: "L",
    center_left: "CL",
    center: "C",
    center_right: "CR",
    right: "R",
    unknown: "?",
  };
  return labels[bias] || "?";
}

export default function SourceBadge({ source }: { source: SourceInfo }) {
  return (
    <div className="flex items-center gap-2 text-xs">
      {/* Credibility score */}
      <span
        className={`px-2 py-0.5 rounded-md border font-mono ${credibilityColor(source.credibility_score)}`}
        title={`Credibility: ${(source.credibility_score * 100).toFixed(0)}%`}
      >
        {(source.credibility_score * 100).toFixed(0)}%
      </span>

      {/* Source type */}
      <span className="text-angel-muted capitalize">{source.source_type}</span>

      {/* Bias indicator */}
      {source.bias_label !== "unknown" && (
        <span
          className={`font-mono ${biasColor(source.bias_label)}`}
          title={`Bias: ${source.bias_label.replace("_", " ")}`}
        >
          [{biasLabel(source.bias_label)}]
        </span>
      )}

      {/* Domain */}
      <span className="text-angel-muted">{source.domain}</span>
    </div>
  );
}
