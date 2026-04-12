const ENGINES = [
  {
    name: "Search Angel",
    queryLogging: "Never",
    ipTracking: "Hashed + rotated daily",
    cookies: "None",
    profiling: "Never",
    ads: "None",
    openSource: "Yes",
    score: "100/100",
    highlight: true,
  },
  {
    name: "Google",
    queryLogging: "18 months",
    ipTracking: "Full IP stored",
    cookies: "Extensive",
    profiling: "Full behavioral",
    ads: "Targeted",
    openSource: "No",
    score: "15/100",
  },
  {
    name: "Bing",
    queryLogging: "6 months",
    ipTracking: "Full IP stored",
    cookies: "Extensive",
    profiling: "Cross-device",
    ads: "Targeted",
    openSource: "No",
    score: "20/100",
  },
  {
    name: "DuckDuckGo",
    queryLogging: "Never",
    ipTracking: "Not stored",
    cookies: "Minimal",
    profiling: "Never",
    ads: "Contextual",
    openSource: "Partial",
    score: "85/100",
  },
];

const ROWS = [
  { key: "queryLogging", label: "Query Logging" },
  { key: "ipTracking", label: "IP Tracking" },
  { key: "cookies", label: "Cookies" },
  { key: "profiling", label: "Behavioral Profiling" },
  { key: "ads", label: "Advertisements" },
  { key: "openSource", label: "Open Source" },
  { key: "score", label: "Privacy Score" },
] as const;

export default function ComparisonTable() {
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-angel-border">
            <th className="text-left py-3 px-4 text-angel-muted font-normal">Feature</th>
            {ENGINES.map((e) => (
              <th
                key={e.name}
                className={`text-center py-3 px-4 font-medium ${
                  e.highlight ? "text-angel-accent" : "text-angel-text"
                }`}
              >
                {e.name}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {ROWS.map((row) => (
            <tr key={row.key} className="border-b border-angel-border/50">
              <td className="py-3 px-4 text-angel-muted">{row.label}</td>
              {ENGINES.map((engine) => {
                const value = engine[row.key as keyof typeof engine] as string;
                const isGood =
                  value === "Never" ||
                  value === "None" ||
                  value === "Yes" ||
                  value === "100/100";
                const isBad =
                  value.includes("months") ||
                  value === "Full IP stored" ||
                  value === "Extensive" ||
                  value.includes("behavioral") ||
                  value.includes("Cross") ||
                  value === "Targeted";

                return (
                  <td
                    key={`${engine.name}-${row.key}`}
                    className={`text-center py-3 px-4 font-mono text-xs ${
                      isGood
                        ? "text-angel-green"
                        : isBad
                          ? "text-angel-red"
                          : "text-angel-text"
                    }`}
                  >
                    {value}
                  </td>
                );
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
