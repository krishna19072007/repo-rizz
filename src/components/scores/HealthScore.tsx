"use client";

import { motion } from "framer-motion";
import { cn, scoreToColor, scoreToLabel } from "@/lib/utils";

interface HealthScoreProps {
  score: number;
  status: string;
  summary: string;
}

export function HealthScore({ score, status, summary }: HealthScoreProps) {
  const color = scoreToColor(score);
  const label = scoreToLabel(score);
  const circumference = 2 * Math.PI * 60;
  const offset = circumference - (score / 100) * circumference;

  return (
    <div className="text-center">
      <motion.div
        initial={{ scale: 0.8, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        transition={{ duration: 0.6, ease: "easeOut" }}
        className="relative inline-flex items-center justify-center"
      >
        <svg width="160" height="160" viewBox="0 0 160 160">
          {/* Background ring */}
          <circle
            cx="80"
            cy="80"
            r="60"
            fill="none"
            stroke="rgba(255,255,255,0.05)"
            strokeWidth="6"
          />
          {/* Score ring */}
          <motion.circle
            cx="80"
            cy="80"
            r="60"
            fill="none"
            stroke={color}
            strokeWidth="6"
            strokeLinecap="round"
            strokeDasharray={circumference}
            strokeDashoffset={circumference}
            transform="rotate(-90 80 80)"
            animate={{ strokeDashoffset: offset }}
            transition={{ duration: 1.5, ease: "easeOut", delay: 0.3 }}
          />
          {/* Glow */}
          <circle
            cx="80"
            cy="80"
            r="60"
            fill="none"
            stroke={color}
            strokeWidth="2"
            opacity={0.2}
            filter="blur(4px)"
          />
        </svg>

        {/* Score text */}
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <motion.span
            className="text-4xl font-bold font-mono"
            style={{ color }}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.5 }}
          >
            {score}
          </motion.span>
          <span className="text-[10px] font-mono" style={{ color: "var(--text-secondary)" }}>
            / 100
          </span>
        </div>
      </motion.div>

      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.8 }}
        className="mt-4"
      >
        <div
          className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-mono font-bold"
          style={{ background: `${color}15`, color }}
        >
          {label}
        </div>
      </motion.div>

      <motion.p
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 1 }}
        className="mt-4 text-sm max-w-md mx-auto"
        style={{ color: "var(--text-secondary)" }}
      >
        {summary}
      </motion.p>
    </div>
  );
}
