"use client";

import { useState, useEffect, useCallback, useMemo, Suspense } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import { AnalysisPipeline } from "@/components/analysis/AnalysisPipeline";
import { DimensionFingerprint } from "@/components/fingerprint/DimensionFingerprint";
import { DimensionCard } from "@/components/scores/DimensionCard";
import { ResumeReadinessHero } from "@/components/scores/ResumeReadinessHero";
import { RizzVerdict } from "@/components/findings/RizzVerdict";
import { ScoringDebugPanel } from "@/components/debug/ScoringDebugPanel";
import { AnalysisResult } from "@/lib/types";
import { parseGitHubUrl } from "@/lib/validators";
import { ArrowLeft, ExternalLink, RotateCcw } from "lucide-react";
import Link from "next/link";

function AnalyzeContent() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const repoParam = searchParams.get("repo");
  const demoParam = searchParams.get("demo");

  const [phase, setPhase] = useState<"input" | "analyzing" | "results">(
    demoParam ? "analyzing" : repoParam ? "analyzing" : "input"
  );
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isDemo, setIsDemo] = useState(!!demoParam);

  const parsed = useMemo(
    () => (repoParam ? parseGitHubUrl(repoParam) : null),
    [repoParam]
  );

  const runAnalysis = useCallback(async () => {
    try {
      setPhase("analyzing");
      setError(null);

            const body: Record<string, unknown> = {};
      if (demoParam) {
        body.demo = true;
        body.owner = "demo";
        body.name = "demo";
      } else if (parsed) {
        body.owner = parsed.owner;
        body.name = parsed.name;
      }

      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8001";
      
      let response;
      try {
        response = await fetch(`${apiUrl}/analyze`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(body),
        });
      } catch (err) {
        throw new Error("Python analysis backend is unavailable");
      }

      const data = await response.json();

      if (!response.ok) {
        if (response.status === 404) {
          throw new Error("repository not found");
        }
        if (response.status === 403) {
          throw new Error(data.message || "GitHub rate limit exceeded");
        }
        // Show actual backend error message when available
        throw new Error(data.detail || data.error || "Analysis failed");
      }

      setResult(data.result);
      setIsDemo(!!data.demo);
      setPhase("results");
    } catch (err) {
      setError(err instanceof Error ? err.message : "An unexpected error occurred");
      setPhase("results");
    }
  }, [parsed, demoParam]);

  useEffect(() => {
    if ((parsed || demoParam) && phase === "analyzing") {
      const timer = setTimeout(runAnalysis, 4000);
      return () => clearTimeout(timer);
    }
  }, [parsed, demoParam, phase, runAnalysis]);

  if (phase === "input") {
    return <InputView />;
  }

  if (phase === "analyzing" && !parsed && !demoParam) {
    return (
      <div className="min-h-screen flex items-center justify-center px-6 pt-20" style={{ background: "var(--bg)" }}>
        <div className="max-w-xl w-full text-center">
          <div className="p-8 rounded-2xl border border-coral/30" style={{ background: "var(--surface)" }}>
            <p className="text-lg font-semibold mb-2" style={{ color: "var(--coral)" }}>
              Invalid Repository
            </p>
            <p className="text-sm mb-6" style={{ color: "var(--text-secondary)" }}>
              &quot;{repoParam}&quot; doesn&apos;t look like a valid public GitHub repository.
            </p>
            <Link
              href="/analyze"
              className="inline-flex items-center gap-2 text-sm font-medium px-4 py-2 rounded-lg transition-colors"
              style={{ background: "var(--surface-elevated)", color: "var(--text)" }}
            >
              <RotateCcw className="w-4 h-4" />
              Try Again
            </Link>
          </div>
        </div>
      </div>
    );
  }

  if (phase === "analyzing" && parsed) {
    return (
      <div className="min-h-screen flex items-center justify-center px-6 pt-20" style={{ background: "var(--bg)" }}>
        <AnalysisPipeline owner={parsed.owner} name={parsed.name} onComplete={() => {}} />
      </div>
    );
  }

  if (phase === "analyzing" && demoParam) {
    return (
      <div className="min-h-screen flex items-center justify-center px-6 pt-20" style={{ background: "var(--bg)" }}>
        <AnalysisPipeline owner="vercel" name="next.js" onComplete={() => {}} />
      </div>
    );
  }

  return <ResultsView result={result} error={error} isDemo={isDemo} />;
}

function InputView() {
  const router = useRouter();

  return (
    <div className="min-h-screen flex items-center justify-center px-6 pt-20" style={{ background: "var(--bg)" }}>
      <div className="max-w-xl w-full text-center">
        <Link
          href="/"
          className="inline-flex items-center gap-2 text-sm mb-8 transition-colors hover:text-lime"
          style={{ color: "var(--text-secondary)" }}
        >
          <ArrowLeft className="w-4 h-4" />
          Back to home
        </Link>

        <h1 className="text-4xl font-bold mb-4" style={{ color: "var(--text)" }}>
          Analyze Repository
        </h1>
        <p className="text-sm mb-8" style={{ color: "var(--text-secondary)" }}>
          Enter a public GitHub repository URL to get a full engineering health report.
        </p>

        <div className="p-6 rounded-2xl border border-border" style={{ background: "var(--surface)" }}>
          <div className="flex items-center gap-2">
            <span className="font-mono text-sm" style={{ color: "var(--text-secondary)" }}>github.com/</span>
            <input
              type="text"
              placeholder="owner/repository"
              className="flex-1 bg-transparent outline-none font-mono text-sm"
              style={{ color: "var(--text)" }}
              onKeyDown={(e) => {
                if (e.key === "Enter") {
                  const value = (e.target as HTMLInputElement).value;
                  const parsed = parseGitHubUrl(value);
                  if (parsed) {
                    router.push(`/analyze?repo=${parsed.owner}/${parsed.name}`);
                  }
                }
              }}
            />
          </div>
        </div>

        <div className="mt-6 flex items-center justify-center gap-4">
          <button
            onClick={() => router.push("/analyze?demo=true")}
            className="text-xs font-mono transition-colors hover:text-lime"
            style={{ color: "var(--text-secondary)" }}
          >
            TRY DEMO →
          </button>
        </div>
      </div>
    </div>
  );
}

function ResultsView({
  result,
  error,
  isDemo,
}: {
  result: AnalysisResult | null;
  error: string | null;
  isDemo: boolean;
}) {
  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center px-6 pt-20" style={{ background: "var(--bg)" }}>
        <div className="max-w-xl w-full text-center">
          <div className="p-8 rounded-2xl border border-coral/30" style={{ background: "var(--surface)" }}>
            <p className="text-lg font-semibold mb-2" style={{ color: "var(--coral)" }}>
              Analysis Failed
            </p>
            <p className="text-sm mb-6" style={{ color: "var(--text-secondary)" }}>
              {error}
            </p>
            <div className="flex items-center justify-center gap-4">
              <Link
                href="/analyze"
                className="flex items-center gap-2 text-sm font-medium px-4 py-2 rounded-lg transition-colors"
                style={{ background: "var(--surface-elevated)", color: "var(--text)" }}
              >
                <RotateCcw className="w-4 h-4" />
                Try Again
              </Link>
              <Link
                href="/"
                className="text-sm transition-colors hover:text-lime"
                style={{ color: "var(--text-secondary)" }}
              >
                Go Home
              </Link>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (!result) {
    return (
      <div className="min-h-screen flex items-center justify-center px-6 pt-20" style={{ background: "var(--bg)" }}>
        <p style={{ color: "var(--text-secondary)" }}>Loading results...</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen pt-20 pb-32" style={{ background: "var(--bg)" }}>
      {/* Demo banner */}
      {isDemo && (
        <div
          className="py-3 text-center text-xs font-mono"
          style={{ background: "var(--violet-dim)", color: "var(--violet)" }}
        >
          DEMO ANALYSIS — Using fixture data, not live GitHub data
        </div>
      )}

      <div className="w-full max-w-[1600px] mx-auto px-4 md:px-8 lg:w-[90vw] lg:px-0">
        {/* Header */}
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="pt-10 mb-4">
          <div className="flex items-center justify-between mb-4">
            <Link
              href="/analyze"
              className="flex items-center gap-2 text-sm transition-colors hover:text-lime"
              style={{ color: "var(--text-secondary)" }}
            >
              <ArrowLeft className="w-4 h-4" />
              Analyze Another
            </Link>
            <a
              href={result.repository.url}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-2 text-sm transition-colors hover:text-lime"
              style={{ color: "var(--text-secondary)" }}
            >
              View on GitHub
              <ExternalLink className="w-3 h-3" />
            </a>
          </div>

          <h1 className="text-2xl md:text-3xl font-bold" style={{ color: "var(--text)" }}>
            {result.repository.owner}/
            <span style={{ color: "var(--lime)" }}>{result.repository.name}</span>
          </h1>
          {result.repository.description && (
            <p className="mt-1 text-sm" style={{ color: "var(--text-secondary)" }}>
              {result.repository.description}
            </p>
          )}

          {/* Repository type badge */}
          <div className="mt-3 flex items-center gap-3 flex-wrap">
            <div
              className="flex items-center gap-2 px-3 py-1 rounded-lg"
              style={{ background: "var(--surface)", border: "1px solid var(--border)" }}
            >
              <span className="text-[10px] font-mono" style={{ color: "var(--text-secondary)" }}>
                REPOSITORY TYPE
              </span>
              <span className="text-xs font-mono font-bold" style={{ color: "var(--lime)" }}>
                {result.repositoryType?.type?.replace(/_/g, " ") || "GENERAL"}
              </span>
              {result.repositoryType?.confidence !== undefined && (
                <span className="text-[10px] font-mono" style={{ color: "var(--text-secondary)" }}>
                  ({(result.repositoryType.confidence * 100).toFixed(0)}% confidence)
                </span>
              )}
            </div>
          </div>
        </motion.div>

        {/* === RESUME READINESS HERO === */}
        <div className="mb-12">
          <ResumeReadinessHero
            score={result.resumeReadinessScore}
            status={result.resumeReadinessStatus}
            summary={result.resumeReadinessSummary}
            strengths={result.resumeReadinessStrengths}
            weaknesses={result.resumeReadinessWeaknesses}
            beforeResume={result.resumeReadinessBeforeResume}
            dimension={result.resumeReadinessDimension}
          />
        </div>

        {/* Rizz Verdict */}
        <div className="mb-16">
          <RizzVerdict verdict={result.rizzVerdict} aiVerdict={result.aiRizzVerdict} />
        </div>

        {/* === 4-AXIS RADAR === */}
        <div className="mb-16">
          <h2
            className="text-xs font-mono tracking-[0.3em] mb-6"
            style={{ color: "var(--text-secondary)" }}
          >
            ENGINEERING HEALTH
          </h2>
          <div className="flex items-center justify-center">
            <DimensionFingerprint dimensions={result.dimensions} />
          </div>
        </div>

        {/* === 4 ENGINEERING DIMENSIONS === */}
        <div className="mb-16">
          <h2
            className="text-xs font-mono tracking-[0.3em] mb-6"
            style={{ color: "var(--text-secondary)" }}
          >
            DIMENSION BREAKDOWN
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {result.engineeringDimensions.map((dim, i) => (
              <DimensionCard key={dim.id} dimension={dim} index={i} />
            ))}
          </div>
        </div>

        {/* Recommendations */}
        {result.recommendations.length > 0 && (
          <div className="mb-16">
            <h2
              className="text-xs font-mono tracking-[0.3em] mb-6"
              style={{ color: "var(--text-secondary)" }}
            >
              FIX THESE BEFORE YOUR RESUME
            </h2>
            <div className="space-y-4">
              {result.recommendations.map((rec, i) => (
                <motion.div
                  key={rec.id}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: i * 0.05 }}
                  className="p-4 rounded-xl border border-border flex items-start gap-4"
                  style={{ background: "var(--surface)" }}
                >
                  <span
                    className="w-6 h-6 rounded-full flex items-center justify-center text-[10px] font-mono font-bold flex-shrink-0 mt-0.5"
                    style={{
                      background: rec.priority === "critical" || rec.priority === "high" ? "var(--coral)" : "var(--blue)",
                      color: "var(--bg)",
                    }}
                  >
                    {i + 1}
                  </span>
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <h3 className="text-sm font-semibold" style={{ color: "var(--text)" }}>
                        {rec.title}
                      </h3>
                      <span
                        className="text-[10px] font-mono px-2 py-0.5 rounded"
                        style={{ color: "var(--text-secondary)", background: "var(--surface-elevated)" }}
                      >
                        {rec.category}
                      </span>
                    </div>
                    <p className="text-xs" style={{ color: "var(--text-secondary)" }}>
                      {rec.description}
                    </p>
                    {rec.impact && (
                      <p className="text-xs font-mono mt-1" style={{ color: "var(--lime)" }}>
                        {rec.impact}
                      </p>
                    )}
                  </div>
                </motion.div>
              ))}
            </div>
          </div>
        )}

        {/* AI Summary */}
        {result.aiSummary && (
          <div className="mb-16 p-6 rounded-2xl border border-border" style={{ background: "var(--surface)" }}>
            <p className="text-[10px] font-mono tracking-[0.2em] mb-2" style={{ color: "var(--violet)" }}>
              AI INTERPRETATION
            </p>
            <p className="text-sm" style={{ color: "var(--text-secondary)" }}>
              {result.aiSummary}
            </p>
          </div>
        )}

        {/* Debug panel */}
        <ScoringDebugPanel result={result} />

        {/* Footer */}
        <div className="text-center pt-8 border-t border-border space-y-3">
          <p className="text-xs font-mono" style={{ color: "var(--text-secondary)" }}>
            DETERMINISTIC ANALYSIS · Scoring model v{result.scoringVersion || "3.0"} · Completed in {result.analysisTimeMs}ms ·{" "}
            {result.aiUnavailable
              ? "AI insights unavailable — deterministic analysis is still available"
              : "AI-assisted insights enabled"}
          </p>
          {result.limitations && result.limitations.length > 0 && (
            <div className="max-w-2xl mx-auto text-left">
              <p className="text-[10px] font-mono mb-1" style={{ color: "var(--text-secondary)" }}>
                LIMITATIONS:
              </p>
              <ul className="space-y-0.5">
                {[...new Set(result.limitations)].map((lim, i) => (
                  <li key={i} className="text-[10px] font-mono" style={{ color: "var(--text-secondary)", opacity: 0.7 }}>
                    · {lim}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default function AnalyzePage() {
  return (
    <Suspense
      fallback={
        <div className="min-h-screen flex items-center justify-center" style={{ background: "var(--bg)" }}>
          <p style={{ color: "var(--text-secondary)" }}>Loading...</p>
        </div>
      }
    >
      <AnalyzeContent />
    </Suspense>
  );
}
