"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { AnalysisResult } from "@/lib/types";

interface ScoringDebugPanelProps {
  result: AnalysisResult;
}

export function ScoringDebugPanel({ result }: ScoringDebugPanelProps) {
  const [expanded, setExpanded] = useState(false);

  // Only show in development
  if (process.env.NODE_ENV !== "development") return null;

  const contributions = result.weightedContributions || [];
  const totalContribution = contributions.reduce((sum, c) => sum + c.contribution, 0);
  const contributionSum = Math.round(totalContribution * 10) / 10;
  const engScore = contributions
    .filter(c => c.applicable)
    .reduce((sum, c) => sum + c.contribution, 0);
  const diff = Math.abs(contributionSum - engScore);

  return (
    <div className="mb-8">
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full text-left p-3 rounded-xl border border-dashed transition-colors"
        style={{
          borderColor: "var(--violet)",
          background: expanded ? "var(--surface)" : "transparent",
        }}
      >
        <div className="flex items-center justify-between">
          <span className="text-[10px] font-mono" style={{ color: "var(--violet)" }}>
            🔧 SCORING DEBUG (dev only)
          </span>
          <span className="text-[10px] font-mono" style={{ color: "var(--text-secondary)" }}>
            {expanded ? "▲ Collapse" : "▼ Expand"}
          </span>
        </div>
      </button>

      <AnimatePresence>
        {expanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            className="overflow-hidden"
          >
            <div
              className="mt-2 p-4 rounded-xl border space-y-4"
              style={{ borderColor: "var(--violet)", background: "var(--surface)" }}
            >
              {/* Repository Type */}
              <div>
                <p className="text-[10px] font-mono mb-1" style={{ color: "var(--text-secondary)" }}>
                  REPOSITORY TYPE
                </p>
                <p className="text-sm font-mono font-bold" style={{ color: "var(--violet)" }}>
                  {result.repositoryType?.type?.replace(/_/g, " ") || "UNKNOWN"}
                  <span className="font-normal ml-2" style={{ color: "var(--text-secondary)" }}>
                    ({(result.repositoryType?.confidence ?? 0) * 100}% confidence)
                  </span>
                </p>
              </div>

              {/* Resume Readiness vs Engineering Score */}
              <div className="flex gap-6">
                <div>
                  <p className="text-[10px] font-mono" style={{ color: "var(--text-secondary)" }}>
                    RESUME READINESS
                  </p>
                  <p className="text-lg font-mono font-bold" style={{ color: "var(--lime)" }}>
                    {result.resumeReadinessScore}
                  </p>
                </div>
                <div>
                  <p className="text-[10px] font-mono" style={{ color: "var(--text-secondary)" }}>
                    ENGINEERING HEALTH
                  </p>
                  <p className="text-lg font-mono font-bold" style={{ color: "var(--blue)" }}>
                    {Math.round(engScore)}
                  </p>
                </div>
                <div>
                  <p className="text-[10px] font-mono" style={{ color: "var(--text-secondary)" }}>
                    APPLICABLE DIMS
                  </p>
                  <p className="text-lg font-mono font-bold" style={{ color: "var(--lime)" }}>
                    {result.applicableDimensions ?? "??"}
                  </p>
                </div>
              </div>

              {/* Weights Table */}
              <div>
                <p className="text-[10px] font-mono mb-2" style={{ color: "var(--text-secondary)" }}>
                  WEIGHTED CONTRIBUTIONS (4 Engineering Dims)
                </p>
                <div className="overflow-x-auto">
                  <table className="w-full text-[11px] font-mono">
                    <thead>
                      <tr style={{ color: "var(--text-secondary)" }}>
                        <th className="text-left py-1 pr-4">Dimension</th>
                        <th className="text-right py-1 px-2">Score</th>
                        <th className="text-right py-1 px-2">Weight</th>
                        <th className="text-right py-1 px-2">Contribution</th>
                        <th className="text-center py-1 px-2">Status</th>
                      </tr>
                    </thead>
                    <tbody>
                      {contributions.map((c) => (
                        <tr
                          key={c.dimension}
                          style={{
                            color: c.applicable ? "var(--text)" : "var(--text-secondary)",
                            opacity: c.applicable ? 1 : 0.5,
                          }}
                        >
                          <td className="py-1 pr-4 capitalize">{c.dimension.replace(/([A-Z])/g, " $1").trim()}</td>
                          <td className="text-right py-1 px-2">{c.applicable ? c.score.toFixed(0) : "—"}</td>
                          <td className="text-right py-1 px-2">{c.applicable ? `${c.effectiveWeight.toFixed(1)}%` : "0%"}</td>
                          <td className="text-right py-1 px-2" style={{ color: c.applicable ? "var(--lime)" : "var(--text-secondary)" }}>
                            {c.applicable ? `+${c.contribution.toFixed(1)}` : "N/A"}
                          </td>
                          <td className="text-center py-1 px-2">
                            {c.applicable ? "✓" : "N/A"}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

              {/* Mathematical Verification */}
              <div className="pt-3 border-t" style={{ borderColor: "var(--border)" }}>
                <p className="text-[10px] font-mono mb-2" style={{ color: "var(--text-secondary)" }}>
                  MATHEMATICAL VERIFICATION
                </p>
                <div className="space-y-1">
                  <p className="text-sm font-mono" style={{ color: "var(--text)" }}>
                    Engineering contributions sum: <span className="font-bold">{contributionSum.toFixed(1)}</span>
                  </p>
                  <p className="text-sm font-mono" style={{ color: "var(--text)" }}>
                    Engineering health score: <span className="font-bold">{Math.round(engScore)}</span>
                  </p>
                  <p className="text-sm font-mono" style={{ color: "var(--text)" }}>
                    Resume Readiness (portfolio): <span className="font-bold">{result.resumeReadinessScore}</span>
                  </p>
                  <p
                    className="text-sm font-mono font-bold"
                    style={{ color: diff < 2 ? "var(--lime)" : "var(--coral)" }}
                  >
                    {diff < 2
                      ? "✓ Contributions sum matches engineering score"
                      : `⚠ Discrepancy: ${diff.toFixed(1)} points (acceptable with rounding)`}
                  </p>
                </div>
              </div>

              {/* Scoring Version */}
              <div className="flex gap-4 text-[10px] font-mono" style={{ color: "var(--text-secondary)" }}>
                <span>Scoring model: v{result.scoringVersion || "3.0"}</span>
                <span>Analysis time: {result.analysisTimeMs}ms</span>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
