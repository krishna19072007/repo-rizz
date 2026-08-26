"use client";

import { motion } from "framer-motion";
import {
  ResumeReadinessStatus,
  getResumeReadinessLabel,
  getResumeReadinessColor,
  DimensionScore,
} from "@/lib/types";

interface ResumeReadinessHeroProps {
  score: number;
  status: ResumeReadinessStatus;
  summary: string;
  strengths: string[];
  weaknesses: string[];
  beforeResume: string[];
  dimension: DimensionScore;
}

export function ResumeReadinessHero({
  score,
  status,
  summary,
}: ResumeReadinessHeroProps) {
  const statusLabel = getResumeReadinessLabel(status);
  const statusColor = getResumeReadinessColor(status);
  const circumference = 2 * Math.PI * 90;
  const offset = circumference - (score / 100) * circumference;

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6, ease: "easeOut" }}
      className="text-center py-8 md:py-12"
    >
      {/* Label */}
      <motion.p
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.1 }}
        className="text-[11px] font-mono tracking-[0.5em] mb-8"
        style={{ color: "var(--text-secondary)" }}
      >
        RESUME READINESS
      </motion.p>

      {/* Large score ring */}
      <motion.div
        initial={{ scale: 0.85, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        transition={{ duration: 0.7, ease: "easeOut", delay: 0.2 }}
        className="relative inline-flex items-center justify-center mb-6"
      >
        <svg width="220" height="220" viewBox="0 0 220 220">
          {/* Background ring */}
          <circle
            cx="110" cy="110" r="90"
            fill="none" stroke="rgba(255,255,255,0.06)" strokeWidth="7"
          />
          {/* Score ring */}
          <motion.circle
            cx="110" cy="110" r="90"
            fill="none" stroke={statusColor}
            strokeWidth="7" strokeLinecap="round"
            strokeDasharray={circumference} strokeDashoffset={circumference}
            transform="rotate(-90 110 110)"
            animate={{ strokeDashoffset: offset }}
            transition={{ duration: 1.4, ease: "easeOut", delay: 0.4 }}
          />
          {/* Glow */}
          <circle
            cx="110" cy="110" r="90"
            fill="none" stroke={statusColor}
            strokeWidth="3" opacity={0.15} filter="blur(6px)"
          />
        </svg>

        {/* Score text */}
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <motion.span
            className="text-7xl font-bold font-mono leading-none"
            style={{ color: statusColor }}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.6 }}
          >
            {score}
          </motion.span>
          <span className="text-sm font-mono mt-1" style={{ color: "var(--text-secondary)" }}>
            / 100
          </span>
        </div>
      </motion.div>

      {/* Status badge */}
      <motion.div
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.9 }}
        className="mb-5"
      >
        <span
          className="inline-block px-5 py-1.5 rounded-full text-sm font-mono font-bold tracking-wider"
          style={{ background: `${statusColor}18`, color: statusColor }}
        >
          {statusLabel}
        </span>
      </motion.div>

      {/* Summary */}
      <motion.p
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 1.1 }}
        className="text-sm max-w-2xl mx-auto"
        style={{ color: "var(--text-secondary)" }}
      >
        {summary}
      </motion.p>
    </motion.div>
  );
}
