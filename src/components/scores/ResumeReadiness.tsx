"use client";

import { motion } from "framer-motion";
import { Check, X, ArrowRight } from "lucide-react";
import { ResumeReadiness as ResumeReadinessType } from "@/lib/types";
import { cn, scoreToColor, scoreToLabel } from "@/lib/utils";

interface ResumeReadinessProps {
  data: ResumeReadinessType;
}

export function ResumeReadiness({ data }: ResumeReadinessProps) {
  const color = scoreToColor(data.score);
  const label = scoreToLabel(data.score);

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.3 }}
      className="border border-border rounded-2xl p-6 md:p-8"
      style={{ background: "var(--surface)" }}
    >
      <div className="flex items-center gap-3 mb-6">
        <span className="text-2xl">📋</span>
        <div>
          <h3 className="text-lg font-semibold" style={{ color: "var(--text)" }}>
            Resume Readiness
          </h3>
          <div className="flex items-center gap-2 mt-1">
            <span
              className="text-3xl font-bold font-mono"
              style={{ color }}
            >
              {data.score}
            </span>
            <span className="text-sm" style={{ color: "var(--text-secondary)" }}>
              / 100
            </span>
            <span
              className="text-[10px] font-mono font-bold px-2 py-0.5 rounded ml-2"
              style={{ background: `${color}15`, color }}
            >
              {label}
            </span>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Strengths */}
        <div>
          <h4
            className="text-xs font-mono font-semibold mb-3"
            style={{ color: "var(--lime)" }}
          >
            STRENGTHS
          </h4>
          <ul className="space-y-2">
            {data.strengths.map((s, i) => (
              <li
                key={i}
                className="flex items-start gap-2 text-xs"
              >
                <Check
                  className="w-3 h-3 mt-0.5 flex-shrink-0"
                  style={{ color: "var(--lime)" }}
                />
                <span style={{ color: "var(--text-secondary)" }}>{s}</span>
              </li>
            ))}
          </ul>
        </div>

        {/* Weaknesses */}
        <div>
          <h4
            className="text-xs font-mono font-semibold mb-3"
            style={{ color: "var(--coral)" }}
          >
            WEAKNESSES
          </h4>
          <ul className="space-y-2">
            {data.weaknesses.map((w, i) => (
              <li
                key={i}
                className="flex items-start gap-2 text-xs"
              >
                <X
                  className="w-3 h-3 mt-0.5 flex-shrink-0"
                  style={{ color: "var(--coral)" }}
                />
                <span style={{ color: "var(--text-secondary)" }}>{w}</span>
              </li>
            ))}
          </ul>
        </div>
      </div>

      {/* Action items */}
      {data.beforeYouPutThisOnResume.length > 0 && (
        <div className="mt-6 pt-4 border-t border-border">
          <h4
            className="text-xs font-mono font-semibold mb-3"
            style={{ color: "var(--text)" }}
          >
            BEFORE YOU PUT THIS ON YOUR RESUME
          </h4>
          <ol className="space-y-2">
            {data.beforeYouPutThisOnResume.map((item, i) => (
              <li
                key={i}
                className="flex items-center gap-3 text-xs"
              >
                <span
                  className="w-5 h-5 rounded-full flex items-center justify-center text-[10px] font-mono font-bold flex-shrink-0"
                  style={{ background: "var(--lime)", color: "var(--bg)" }}
                >
                  {i + 1}
                </span>
                <span style={{ color: "var(--text)" }}>{item}</span>
              </li>
            ))}
          </ol>
        </div>
      )}
    </motion.div>
  );
}
