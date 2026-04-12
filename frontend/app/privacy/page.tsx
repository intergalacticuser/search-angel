import Header from "@/components/Header";
import ComparisonTable from "@/components/ComparisonTable";
import PrivacyNotice from "@/components/PrivacyNotice";

export default function PrivacyPage() {
  return (
    <div className="min-h-screen flex flex-col">
      <Header />

      <main className="flex-1 max-w-4xl mx-auto w-full px-4 py-12">
        {/* Hero */}
        <div className="text-center mb-12">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img
            src="/logo.png"
            alt="Search Angel"
            width={120}
            height={80}
            className="mx-auto mb-4"
          />
          <h1 className="text-3xl font-bold text-angel-text mb-3">
            Your Privacy is Sacred
          </h1>
          <p className="text-angel-muted text-lg max-w-2xl mx-auto">
            Search Angel was built from the ground up to prove that powerful search
            doesn&apos;t require surveillance. Here&apos;s exactly what we do and don&apos;t do.
          </p>
        </div>

        {/* Privacy Score */}
        <div className="flex justify-center mb-12">
          <div className="bg-angel-surface border border-angel-green/30 rounded-2xl p-8 text-center">
            <div className="text-6xl font-bold text-angel-green font-mono mb-2">100</div>
            <div className="text-angel-green text-sm font-medium">Privacy Score</div>
            <div className="text-angel-muted text-xs mt-1">out of 100</div>
          </div>
        </div>

        {/* What we DON'T collect */}
        <section className="mb-12">
          <h2 className="text-xl font-semibold text-angel-text mb-6 text-center">
            What We DON&apos;T Collect
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {[
              {
                title: "No Query Logging",
                desc: "Your searches are never stored, never analyzed, never sold. The moment your results are delivered, your query vanishes.",
                icon: "\uD83D\uDD0D",
              },
              {
                title: "No IP Tracking",
                desc: "Your IP address is hashed with a daily-rotating salt for rate limiting only. The raw IP is never stored anywhere.",
                icon: "\uD83C\uDF10",
              },
              {
                title: "No Cookies",
                desc: "We set zero cookies. No session cookies, no tracking cookies, no third-party cookies. Your browser stays clean.",
                icon: "\uD83C\uDF6A",
              },
              {
                title: "No Behavioral Profiling",
                desc: "We don't build profiles, don't track click patterns, don't analyze your browsing behavior. You're anonymous to us.",
                icon: "\uD83D\uDC64",
              },
              {
                title: "No Third-Party Trackers",
                desc: "Zero analytics scripts. No Google Analytics, no Facebook Pixel, no advertising SDKs. Our code is clean.",
                icon: "\uD83D\uDEAB",
              },
              {
                title: "No Data Selling",
                desc: "We will never sell, share, or monetize your search data. Our business model does not depend on your data.",
                icon: "\uD83D\uDCB0",
              },
            ].map((item) => (
              <div
                key={item.title}
                className="p-5 rounded-xl border border-angel-border bg-angel-surface/30"
              >
                <div className="text-2xl mb-2">{item.icon}</div>
                <h3 className="font-medium text-angel-text mb-1">{item.title}</h3>
                <p className="text-sm text-angel-muted">{item.desc}</p>
              </div>
            ))}
          </div>
        </section>

        {/* How search works */}
        <section className="mb-12">
          <h2 className="text-xl font-semibold text-angel-text mb-6 text-center">
            How Your Search Works
          </h2>
          <div className="space-y-4">
            {[
              {
                step: "1",
                title: "Your query arrives",
                desc: "Encrypted in transit. Your IP is immediately hashed and the original discarded. No logs.",
              },
              {
                step: "2",
                title: "Privacy-only search engines",
                desc: "We ONLY use search engines that don't log queries: DuckDuckGo, Brave Search, Startpage, Mojeek, Qwant. Google and Bing are disabled because they log everything.",
              },
              {
                step: "3",
                title: "Results are ranked",
                desc: "Our evidence-based ranking system scores results by credibility, not by ad revenue. Source bias is disclosed.",
              },
              {
                step: "4",
                title: "Results delivered, data erased",
                desc: "You see your results. We forget everything. No query history, no click tracking, no retargeting.",
              },
            ].map((s) => (
              <div
                key={s.step}
                className="flex gap-4 p-4 rounded-xl border border-angel-border bg-angel-surface/20"
              >
                <div className="w-10 h-10 rounded-full bg-angel-accent/10 border border-angel-accent/30 flex items-center justify-center text-angel-accent font-bold shrink-0">
                  {s.step}
                </div>
                <div>
                  <h3 className="font-medium text-angel-text">{s.title}</h3>
                  <p className="text-sm text-angel-muted mt-0.5">{s.desc}</p>
                </div>
              </div>
            ))}
          </div>
        </section>

        {/* Ghost Mode */}
        <section className="mb-12">
          <h2 className="text-xl font-semibold text-angel-text mb-4 text-center">
            Ghost Mode
          </h2>
          <div className="p-6 rounded-xl border border-angel-accent/20 bg-angel-accent/5 text-center">
            <div className="text-4xl mb-3">{"\uD83D\uDC7B"}</div>
            <p className="text-angel-text mb-2">
              Ghost Mode adds an extra layer of privacy for free users.
            </p>
            <p className="text-sm text-angel-muted">
              When enabled: forces private search mode, prevents browser caching of results,
              adds strict no-referrer policy. Toggle it in the search bar.
            </p>
          </div>
        </section>

        {/* Premium Ephemeral Sessions */}
        <section className="mb-12">
          <h2 className="text-xl font-semibold text-angel-text mb-4 text-center">
            Premium: Ephemeral Sessions
          </h2>
          <div className="p-6 rounded-xl border border-amber-500/20 bg-amber-500/5">
            <div className="text-center mb-4">
              <span className="text-xs font-mono text-amber-400 bg-amber-400/10 px-3 py-1 rounded-full border border-amber-400/20">
                COMING SOON
              </span>
            </div>
            <p className="text-angel-text text-center mb-3">
              The ultimate in search privacy: your own isolated Docker container.
            </p>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-sm text-angel-muted">
              <div className="p-3 rounded-lg bg-angel-surface/50 border border-angel-border text-center">
                A fresh container spins up for your session
              </div>
              <div className="p-3 rounded-lg bg-angel-surface/50 border border-angel-border text-center">
                All search data exists only inside it
              </div>
              <div className="p-3 rounded-lg bg-angel-surface/50 border border-angel-border text-center">
                Session ends = container destroyed = zero trace
              </div>
            </div>
          </div>
        </section>

        {/* Comparison Table */}
        <section className="mb-12">
          <h2 className="text-xl font-semibold text-angel-text mb-6 text-center">
            How We Compare
          </h2>
          <div className="rounded-xl border border-angel-border bg-angel-surface/30 overflow-hidden">
            <ComparisonTable />
          </div>
        </section>

        {/* Open Source */}
        <section className="text-center mb-8">
          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full border border-angel-border bg-angel-surface/30">
            <svg className="w-5 h-5 text-angel-text" fill="currentColor" viewBox="0 0 24 24">
              <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/>
            </svg>
            <span className="text-sm text-angel-text">Open Source</span>
          </div>
          <p className="text-xs text-angel-muted mt-2">
            Don&apos;t trust us - verify. Our entire codebase is open for inspection.
          </p>
        </section>
      </main>

      <PrivacyNotice />
    </div>
  );
}
