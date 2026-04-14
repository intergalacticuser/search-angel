"use client";

import { useState, useEffect, useCallback } from "react";
import { buildApiUrl } from "@/lib/api-base";

interface PhantomSession {
  session_id: string;
  status: string;
  port: number;
  ttl_seconds: number;
}

export default function PhantomMode() {
  const [session, setSession] = useState<PhantomSession | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [elapsed, setElapsed] = useState(0);

  // Timer
  useEffect(() => {
    if (!session) return;
    const interval = setInterval(() => {
      setElapsed((e) => e + 1);
    }, 1000);
    return () => clearInterval(interval);
  }, [session]);

  const startPhantom = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(buildApiUrl("/api/v1/phantom/start"), {
        method: "POST",
      });
      if (!res.ok) {
        const data = await res.json();
        throw new Error(data.detail || "Failed to start");
      }
      const data = await res.json();
      setSession(data);
      setElapsed(0);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to start phantom mode");
    } finally {
      setLoading(false);
    }
  }, []);

  const endPhantom = useCallback(async () => {
    if (!session) return;
    try {
      await fetch(buildApiUrl(`/api/v1/phantom/end/${session.session_id}`), {
        method: "DELETE",
      });
    } catch {
      // Best effort
    }
    setSession(null);
    setElapsed(0);
  }, [session]);

  const formatTime = (seconds: number) => {
    const m = Math.floor(seconds / 60);
    const s = seconds % 60;
    return `${m}:${s.toString().padStart(2, "0")}`;
  };

  const remaining = Math.max(0, 1800 - elapsed);

  // Not active - show start button
  if (!session) {
    return (
      <div className="mt-6">
        <button
          onClick={startPhantom}
          disabled={loading}
          className={`group relative w-full max-w-md mx-auto flex items-center justify-center gap-3 px-6 py-4 rounded-2xl border-2 transition-all duration-300 ${
            loading
              ? "border-purple-500/30 bg-purple-500/5 cursor-wait"
              : "border-purple-500/20 bg-purple-500/5 hover:border-purple-500/50 hover:bg-purple-500/10 hover:shadow-lg hover:shadow-purple-500/10 cursor-pointer"
          }`}
        >
          <span className="text-2xl">{loading ? "..." : "\uD83D\uDC7B"}</span>
          <div className="text-left">
            <div className="text-purple-400 font-semibold text-sm">
              {loading ? "Creating Phantom Container..." : "Phantom Mode"}
            </div>
            <div className="text-purple-400/60 text-xs">
              Isolated Docker container. Destroyed after use. Zero trace.
            </div>
          </div>
          <span className="text-purple-400/40 text-xs font-mono">30min</span>
        </button>

        {error && (
          <p className="text-center text-xs text-red-400 mt-2">{error}</p>
        )}
      </div>
    );
  }

  // Active phantom session
  return (
    <div className="mt-6">
      <div className="max-w-md mx-auto rounded-2xl border-2 border-purple-500/40 bg-purple-500/5 overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between px-4 py-3 bg-purple-500/10 border-b border-purple-500/20">
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-purple-400 animate-pulse" />
            <span className="text-purple-400 font-semibold text-sm">Phantom Mode Active</span>
          </div>
          <div className="flex items-center gap-3">
            <span className="text-xs font-mono text-purple-400/70">
              {formatTime(remaining)} remaining
            </span>
            <button
              onClick={endPhantom}
              className="text-xs px-3 py-1 rounded-lg border border-red-500/30 text-red-400 hover:bg-red-500/10 transition-colors"
            >
              Destroy
            </button>
          </div>
        </div>

        {/* Info */}
        <div className="px-4 py-3 space-y-2 text-xs">
          <div className="flex justify-between text-purple-400/70">
            <span>Container</span>
            <span className="font-mono">phantom_{session.session_id.slice(0, 8)}</span>
          </div>
          <div className="flex justify-between text-purple-400/70">
            <span>Status</span>
            <span className="text-purple-400">{session.status}</span>
          </div>

          {/* Progress bar (TTL) */}
          <div className="h-1 bg-purple-500/10 rounded-full mt-2">
            <div
              className="h-full bg-purple-500/50 rounded-full transition-all duration-1000"
              style={{ width: `${(remaining / 1800) * 100}%` }}
            />
          </div>

          <p className="text-purple-400/40 text-[10px] text-center pt-1">
            All searches route through this isolated container.
            When destroyed, zero data remains.
          </p>
        </div>
      </div>
    </div>
  );
}
