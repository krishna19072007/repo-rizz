"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { parseGitHubUrl } from "@/lib/validators";
import { AnalysisResult, getResumeReadinessColor, getResumeReadinessLabel } from "@/lib/types";
import { ArrowRight, GitCompare, ArrowLeft, RotateCcw, ExternalLink } from "lucide-react";
import Link from "next/link";

type CompareState = "input" | "loading" | "results" | "error";

function ScoreBar({
  score,
  maxScore,
  label,
}: {
  score: number;
  maxScore: number;
  label: string;
}) {
  const pct = maxScore > 0 ? (score / maxScore) * 100 : 0;
  const color = pct >= 80 ? "var(--lime)" : pct >= 60 ? "var(--blue)" : pct >= 40 ? "var(--coral)" : "var(--coral)";
  return (
    <div className="space-y-1">
      <div className="flex items-center justify-between">
        <span className="text-[10px] font-mono" style={{ color: "var(--text-secondary)" }}>{label}</span>
        <span className="text-[11px] font-mono font-bold" style={{ color }}>{Math.round(score)}/{maxScore}</span>
      </div>
      <div className="h-1.5 rounded-full overflow-hidden" style={{ background: "var(--surface-elevated)" }}>
        <motion.div className="h-full rounded-full" style={{ background: color }} initial={{ width: 0 }} animate={{ width: `${pct}%` }} transition={{ duration: 0.8, ease: "easeOut" }} />
      </div>
    </div>
  );
}

function CompareRepoCard({ result, side }: { result: AnalysisResult; side: "left" | "right" }) {
  const rrColor = getResumeReadinessColor(result.resumeReadinessStatus);
  return (
    <motion.div
      initial={{ opacity: 0, x: side === "left" ? -20 : 20 }}
      animate={{ opacity: 1, x: 0 }}
      className="rounded-2xl border border-border p-6 space-y-6"
      style={{ background: "var(--surface)" }}
    >
      <div>
        <div className="flex items-center justify-between mb-2">
          <span className="text-[10px] font-mono" style={{ color: "var(--text-secondary)" }}>REPOSITORY {side === "left" ? "1" : "2"}</span>
          <a href={result.repository.url} target="_blank" rel="noopener noreferrer" className="text-[10px] font-mono transition-colors hover:text-lime" style={{ color: "var(--text-secondary)" }}>
            <ExternalLink className="w-3 h-3" />
          </a>
        </div>
        <h3 className="text-lg font-bold" style={{ color: "var(--text)" }}>
          {result.repository.owner}/<span style={{ color: side === "left" ? "var(--lime)" : "var(--violet)" }}>{result.repository.name}</span>
        </h3>
        {result.repository.description && <p className="text-xs mt-1" style={{ color: "var(--text-secondary)" }}>{result.repository.description}</p>}
      </div>

      {/* Resume Readiness Score */}
      <div className="flex items-center gap-4">
        <div className="text-center">
          <p className="text-4xl font-bold font-mono" style={{ color: rrColor }}>{result.resumeReadinessScore}</p>
          <p className="text-[10px] font-mono" style={{ color: "var(--text-secondary)" }}>/100 · {getResumeReadinessLabel(result.resumeReadinessStatus)}</p>
        </div>
        <div className="flex-1">
          <div className="px-2 py-1 rounded text-[10px] font-mono inline-block mb-2" style={{ background: "var(--surface-elevated)", color: "var(--text-secondary)" }}>
            {result.repositoryType?.type?.replace(/_/g, " ") || "GENERAL"}
          </div>
          <p className="text-xs" style={{ color: "var(--text-secondary)" }}>{result.resumeReadinessSummary}</p>
        </div>
      </div>

      {/* Engineering Dimensions */}
      <div className="space-y-3">
        {result.engineeringDimensions.map((dim) => (
          <ScoreBar key={dim.id} score={dim.score} maxScore={dim.maxScore} label={dim.name} />
        ))}
      </div>
    </motion.div>
  );
}

function ComparisonSummary({ repo1, repo2 }: { repo1: AnalysisResult; repo2: AnalysisResult }) {
  const winner = repo1.resumeReadinessScore > repo2.resumeReadinessScore ? 1 : repo1.resumeReadinessScore < repo2.resumeReadinessScore ? 2 : 0;
  const diff = Math.abs(repo1.resumeReadinessScore - repo2.resumeReadinessScore);

  const dimensionWins: { dimension: string; winner: 1 | 2; diff: number }[] = [];
  const allDimIds = new Set([...repo1.engineeringDimensions.map((d) => d.id), ...repo2.engineeringDimensions.map((d) => d.id)]);
  allDimIds.forEach((dimId) => {
    const d1 = repo1.engineeringDimensions.find((d) => d.id === dimId);
    const d2 = repo2.engineeringDimensions.find((d) => d.id === dimId);
    if (d1 && d2) {
      const dDiff = d1.score - d2.score;
      if (Math.abs(dDiff) > 5) {
        dimensionWins.push({ dimension: d1.name, winner: dDiff > 0 ? 1 : 2, diff: Math.abs(dDiff) });
      }
    }
  });

  const rr1Color = getResumeReadinessColor(repo1.resumeReadinessStatus);
  const rr2Color = getResumeReadinessColor(repo2.resumeReadinessStatus);

  return (
    <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.3 }}
      className="rounded-2xl border p-6 space-y-4"
      style={{ background: "var(--surface)", borderColor: winner === 1 ? "var(--lime)" : winner === 2 ? "var(--violet)" : "var(--border)" }}
    >
      <p className="text-[10px] font-mono tracking-[0.2em]" style={{ color: "var(--text-secondary)" }}>COMPARISON VERDICT</p>
      <div className="text-center">
        {winner === 0 ? (
          <p className="text-lg font-bold" style={{ color: "var(--blue)" }}>It&apos;s a tie! Both scored {repo1.resumeReadinessScore}/100</p>
        ) : (
          <p className="text-lg font-bold" style={{ color: winner === 1 ? "var(--lime)" : "var(--violet)" }}>
            {winner === 1 ? repo1.repository.name : repo2.repository.name} wins by {diff} points
          </p>
        )}
      </div>

      {dimensionWins.length > 0 && (
        <div>
          <p className="text-[10px] font-mono mb-2" style={{ color: "var(--text-secondary)" }}>DIMENSION LEADERS</p>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
            {dimensionWins.map((dw) => (
              <div key={dw.dimension} className="flex items-center justify-between p-2 rounded-lg text-xs" style={{ background: "var(--surface-elevated)" }}>
                <span className="font-mono" style={{ color: "var(--text-secondary)" }}>{dw.dimension}</span>
                <span className="font-mono font-bold" style={{ color: dw.winner === 1 ? "var(--lime)" : "var(--violet)" }}>
                  {dw.winner === 1 ? repo1.repository.name : repo2.repository.name} +{dw.diff}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="grid grid-cols-2 gap-4 pt-2">
        <div className="text-center p-3 rounded-lg" style={{ background: "var(--surface-elevated)" }}>
          <p className="text-[10px] font-mono" style={{ color: "var(--text-secondary)" }}>{repo1.repository.name}</p>
          <p className="text-2xl font-bold font-mono" style={{ color: rr1Color }}>{repo1.resumeReadinessScore}</p>
        </div>
        <div className="text-center p-3 rounded-lg" style={{ background: "var(--surface-elevated)" }}>
          <p className="text-[10px] font-mono" style={{ color: "var(--text-secondary)" }}>{repo2.repository.name}</p>
          <p className="text-2xl font-bold font-mono" style={{ color: rr2Color }}>{repo2.resumeReadinessScore}</p>
        </div>
      </div>
    </motion.div>
  );
}

export default function ComparePage() {
  const [repo1, setRepo1] = useState("");
  const [repo2, setRepo2] = useState("");
  const [state, setState] = useState<CompareState>("input");
  const [result1, setResult1] = useState<AnalysisResult | null>(null);
  const [result2, setResult2] = useState<AnalysisResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const runComparison = async () => {
    const p1 = parseGitHubUrl(repo1);
    const p2 = parseGitHubUrl(repo2);
    if (!p1 || !p2) { setError("Please enter two valid GitHub repository URLs."); setState("error"); return; }
    setState("loading"); setError(null);
    try {
      const response = await fetch("/api/github/compare", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ repo1: `${p1.owner}/${p1.name}`, repo2: `${p2.owner}/${p2.name}` }) });
      const data = await response.json();
      if (!response.ok) throw new Error(data.error || "Comparison failed");
      setResult1(data.comparison.repo1); setResult2(data.comparison.repo2); setState("results");
    } catch (err) { setError(err instanceof Error ? err.message : "Comparison failed"); setState("error"); }
  };

  if (state === "results" && result1 && result2) {
    return (
      <div className="min-h-screen pt-20 pb-32" style={{ background: "var(--bg)" }}>
        <div className="max-w-6xl mx-auto px-6">
          <div className="flex items-center justify-between mb-8">
            <button onClick={() => { setState("input"); setResult1(null); setResult2(null); }} className="flex items-center gap-2 text-sm transition-colors hover:text-lime" style={{ color: "var(--text-secondary)" }}>
              <ArrowLeft className="w-4 h-4" /> Compare Again
            </button>
          </div>
          <h1 className="text-3xl font-bold mb-8" style={{ color: "var(--text)" }}>COMPARISON <span style={{ color: "var(--lime)" }}>RESULTS</span></h1>
          <ComparisonSummary repo1={result1} repo2={result2} />
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mt-8">
            <CompareRepoCard result={result1} side="left" />
            <CompareRepoCard result={result2} side="right" />
          </div>
          <div className="text-center pt-8 mt-8 border-t border-border">
            <p className="text-xs font-mono" style={{ color: "var(--text-secondary)" }}>DETERMINISTIC ANALYSIS · Scoring model v{result1.scoringVersion || "3.0"}</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen pt-24 pb-32 px-6" style={{ background: "var(--bg)" }}>
      <div className="max-w-4xl mx-auto">
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="text-center mb-16">
          <Link href="/" className="text-xs font-mono mb-8 inline-block transition-colors hover:text-lime" style={{ color: "var(--text-secondary)" }}>← Back to Home</Link>
          <h1 className="text-4xl md:text-5xl font-bold tracking-tight mb-4" style={{ color: "var(--text)" }}>COMPARE <span style={{ color: "var(--lime)" }}>REPOSITORIES</span></h1>
          <p className="text-sm max-w-lg mx-auto" style={{ color: "var(--text-secondary)" }}>Compare two repositories side-by-side to see how they stack up against each other.</p>
        </motion.div>
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }} className="grid grid-cols-1 md:grid-cols-3 gap-6 items-end">
          <div>
            <label className="text-xs font-mono mb-2 block" style={{ color: "var(--text-secondary)" }}>REPOSITORY 1</label>
            <div className="flex items-center rounded-xl border border-border p-3" style={{ background: "var(--surface)" }}>
              <span className="font-mono text-sm mr-1" style={{ color: "var(--text-secondary)" }}>github.com/</span>
              <input type="text" value={repo1} onChange={(e) => setRepo1(e.target.value)} placeholder="owner/repo" className="flex-1 bg-transparent outline-none font-mono text-sm" style={{ color: "var(--text)" }} onKeyDown={(e) => e.key === "Enter" && repo1 && repo2 && runComparison()} />
            </div>
          </div>
          <div className="flex items-center justify-center pb-2"><GitCompare className="w-6 h-6" style={{ color: "var(--text-secondary)" }} /></div>
          <div>
            <label className="text-xs font-mono mb-2 block" style={{ color: "var(--text-secondary)" }}>REPOSITORY 2</label>
            <div className="flex items-center rounded-xl border border-border p-3" style={{ background: "var(--surface)" }}>
              <span className="font-mono text-sm mr-1" style={{ color: "var(--text-secondary)" }}>github.com/</span>
              <input type="text" value={repo2} onChange={(e) => setRepo2(e.target.value)} placeholder="owner/repo" className="flex-1 bg-transparent outline-none font-mono text-sm" style={{ color: "var(--text)" }} onKeyDown={(e) => e.key === "Enter" && repo1 && repo2 && runComparison()} />
            </div>
          </div>
        </motion.div>
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.4 }} className="text-center mt-8">
          <button disabled={!repo1 || !repo2 || state === "loading"} className="inline-flex items-center gap-2 px-8 py-3 rounded-xl font-semibold text-sm transition-all disabled:opacity-30 hover:scale-[1.02] active:scale-[0.98]" style={{ background: "var(--lime)", color: "var(--bg)" }} onClick={runComparison}>
            {state === "loading" ? <span className="animate-pulse">Analyzing both repositories...</span> : <>COMPARE <ArrowRight className="w-4 h-4" /></>}
          </button>
        </motion.div>
        {state === "error" && error && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="mt-8 p-4 rounded-xl border border-coral/30 text-center" style={{ background: "var(--surface)" }}>
            <p className="text-sm font-semibold mb-1" style={{ color: "var(--coral)" }}>Comparison Failed</p>
            <p className="text-xs" style={{ color: "var(--text-secondary)" }}>{error}</p>
            <button onClick={() => setState("input")} className="inline-flex items-center gap-2 mt-3 text-xs font-mono transition-colors hover:text-lime" style={{ color: "var(--text-secondary)" }}><RotateCcw className="w-3 h-3" /> Try Again</button>
          </motion.div>
        )}
      </div>
    </div>
  );
}
