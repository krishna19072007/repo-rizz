"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { ChevronDown, Check, AlertTriangle, AlertCircle, Info, HelpCircle } from "lucide-react";
import { DimensionScore, Finding } from "@/lib/types";
import { cn, scoreToColor } from "@/lib/utils";
import { getConfidence } from "@/lib/utils";

interface DimensionCardProps {
  dimension: DimensionScore;
  index: number;
}

export function DimensionCard({ dimension, index }: DimensionCardProps) {
  const [isExpanded, setIsExpanded] = useState(false);
  const color = scoreToColor((dimension.score / dimension.maxScore) * 100);
  const pct = Math.round((dimension.score / dimension.maxScore) * 100);

  const circumference = 2 * Math.PI * 22;
  const offset = circumference - (pct / 100) * circumference;

  const confidenceColors = {
    high: "var(--lime)",
    medium: "var(--blue)",
    low: "var(--coral)",
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.05, duration: 0.4 }}
      className="border border-border rounded-xl overflow-hidden transition-colors hover:border-border-strong"
      style={{ background: "var(--surface)" }}
    >
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full flex items-center gap-4 p-5 text-left"
        aria-expanded={isExpanded}
      >
        {/* Score ring */}
        <div className="relative w-12 h-12 flex-shrink-0">
          <svg width="48" height="48" viewBox="0 0 48 48">
            <circle cx="24" cy="24" r="22" fill="none" stroke="rgba(255,255,255,0.05)" strokeWidth="3" />
            <circle cx="24" cy="24" r="22" fill="none" stroke={color} strokeWidth="3" strokeLinecap="round"
              strokeDasharray={circumference} strokeDashoffset={offset} transform="rotate(-90 24 24)"
              className="transition-all duration-700" />
          </svg>
          <span className="absolute inset-0 flex items-center justify-center text-xs font-mono font-bold" style={{ color }}>
            {dimension.score}
          </span>
        </div>

        {/* Info */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <h3 className="text-sm font-semibold uppercase tracking-wide" style={{ color: "var(--text)" }}>
              {dimension.name}
            </h3>
            <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded" style={{ color, background: `${color}15` }}>
              {pct >= 80 ? "STRONG" : pct >= 60 ? "GOOD" : pct >= 40 ? "FAIR" : "WEAK"}
            </span>
          </div>
          <p className="text-xs line-clamp-1" style={{ color: "var(--text-secondary)" }}>
            {dimension.summary}
          </p>
          {/* Key evidence preview — top 3 items */}
          {dimension.evidence.length > 0 && (
            <div className="mt-2 flex flex-col gap-0.5">
              {dimension.evidence.slice(0, 3).map((e, i) => (
                <span key={i} className="text-[10px] font-mono flex items-center gap-1 truncate" style={{ color: "var(--text-secondary)" }}>
                  <span className="flex-shrink-0" style={{ color: e.startsWith("✓") ? "var(--lime)" : "var(--coral)" }}>
                    {e.startsWith("✓") ? "✓" : "✗"}
                  </span>
                  <span className="truncate">{e.replace(/^[✓✗]\s*/, "")}</span>
                </span>
              ))}
            </div>
          )}
        </div>

        {/* Confidence badge */}
        <span className="text-[9px] font-mono px-2 py-0.5 rounded hidden sm:inline-block"
          style={{ color: confidenceColors[dimension.confidence], background: `${confidenceColors[dimension.confidence]}15` }}>
          {getConfidence(dimension.confidence)}
        </span>

        <ChevronDown
          className={cn("w-4 h-4 transition-transform duration-200 flex-shrink-0", isExpanded && "rotate-180")}
          style={{ color: "var(--text-secondary)" }}
        />
      </button>

      <AnimatePresence>
        {isExpanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="overflow-hidden"
          >
            <div className="px-5 pb-5 space-y-4 border-t border-border">
              {/* WHY THIS SCORE? */}
              <div className="pt-4">
                <h4 className="text-xs font-mono font-semibold mb-3 flex items-center gap-2" style={{ color: "var(--lime)" }}>
                  <HelpCircle className="w-3 h-3" />
                  WHY THIS SCORE?
                </h4>

                {/* Score breakdown */}
                <div className="space-y-1 mb-4">
                  {dimension.rulesApplied.map((rule, i) => {
                    const [, value] = rule.split(" = ");
                    const isPositive = value?.startsWith("+") && value !== "+0";
                    return (
                      <div key={i} className="flex items-center justify-between text-xs font-mono">
                        <span style={{ color: "var(--text-secondary)" }}>{rule.split(" = ")[0]}</span>
                        <span style={{ color: isPositive ? "var(--lime)" : "var(--text-secondary)" }}>{value}</span>
                      </div>
                    );
                  })}
                  <div className="flex items-center justify-between text-xs font-mono font-bold pt-1 border-t border-border">
                    <span style={{ color: "var(--text)" }}>TOTAL</span>
                    <span style={{ color }}>{dimension.score} / {dimension.maxScore}</span>
                  </div>
                </div>

                {/* Confidence reason */}
                {dimension.confidenceReason && (
                  <div className="text-[11px] mb-3 p-2 rounded" style={{ background: "var(--bg)", color: "var(--text-secondary)" }}>
                    <span className="font-mono font-semibold" style={{ color: confidenceColors[dimension.confidence] }}>
                      {getConfidence(dimension.confidence)}:{" "}
                    </span>
                    {dimension.confidenceReason}
                  </div>
                )}
              </div>

              {/* Evidence */}
              {dimension.evidence.length > 0 && (
                <div>
                  <h4 className="text-xs font-mono font-semibold mb-2" style={{ color: "var(--text-secondary)" }}>
                    EVIDENCE
                  </h4>
                  <ul className="space-y-1">
                    {dimension.evidence.map((e, i) => (
                      <li key={i} className="text-xs font-mono flex items-start gap-2" style={{ color: "var(--text)" }}>
                        <span className="flex-shrink-0 mt-0.5" style={{
                          color: e.startsWith("✓") ? "var(--lime)" : e.startsWith("✗") ? "var(--coral)" : "var(--text-secondary)"
                        }}>
                          {e.startsWith("✓") ? "•" : e.startsWith("✗") ? "•" : "·"}
                        </span>
                        {e.replace(/^[✓✗]\s*/, "")}
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Findings */}
              {dimension.findings.length > 0 && (
                <div>
                  <h4 className="text-xs font-mono font-semibold mb-2" style={{ color: "var(--text-secondary)" }}>
                    FINDINGS
                  </h4>
                  <div className="space-y-2">
                    {dimension.findings.map(finding => (
                      <FindingItem key={finding.id} finding={finding} />
                    ))}
                  </div>
                </div>
              )}

              {/* Limitations */}
              {dimension.limitations.length > 0 && (
                <div className="p-3 rounded-lg text-xs" style={{ background: "var(--bg)" }}>
                  <span className="font-mono font-semibold" style={{ color: "var(--blue)" }}>
                    LIMITATIONS:{" "}
                  </span>
                  <span style={{ color: "var(--text-secondary)" }}>
                    {dimension.limitations.join("; ")}
                  </span>
                </div>
              )}

              {/* Recommendation */}
              <div className="p-3 rounded-lg text-xs" style={{ background: "var(--surface-elevated)" }}>
                <span className="font-mono font-semibold" style={{ color: "var(--lime)" }}>
                  RECOMMENDATION:{" "}
                </span>
                <span style={{ color: "var(--text-secondary)" }}>
                  {dimension.recommendation}
                </span>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}

function FindingItem({ finding }: { finding: Finding }) {
  const iconMap = {
    critical: <AlertCircle className="w-3 h-3" style={{ color: "var(--coral)" }} />,
    warning: <AlertTriangle className="w-3 h-3" style={{ color: "var(--coral)" }} />,
    info: <Info className="w-3 h-3" style={{ color: "var(--blue)" }} />,
    positive: <Check className="w-3 h-3" style={{ color: "var(--lime)" }} />,
  };

  return (
    <div className="flex items-start gap-2 p-2 rounded" style={{ background: "var(--bg)" }}>
      {iconMap[finding.severity]}
      <div className="flex-1 min-w-0">
        <p className="text-xs font-medium" style={{ color: "var(--text)" }}>{finding.title}</p>
        <p className="text-[11px] mt-0.5" style={{ color: "var(--text-secondary)" }}>{finding.description}</p>
        {finding.recommendation && (
          <p className="text-[11px] mt-1 font-mono" style={{ color: "var(--lime)" }}>→ {finding.recommendation}</p>
        )}
      </div>
    </div>
  );
}
