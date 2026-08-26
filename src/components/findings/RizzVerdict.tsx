"use client";

import { motion } from "framer-motion";
import { Sparkles } from "lucide-react";

interface RizzVerdictProps {
  verdict: string;
  aiVerdict?: string;
}

export function RizzVerdict({ verdict, aiVerdict }: RizzVerdictProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.5, duration: 0.5 }}
      className="relative border border-border rounded-2xl p-8 text-center overflow-hidden"
      style={{ background: "var(--surface)" }}
    >
      {/* Gradient overlay */}
      <div
        className="absolute inset-0 opacity-20"
        style={{
          background:
            "radial-gradient(ellipse at center, rgba(124, 92, 255, 0.15), transparent 70%)",
        }}
      />

      <div className="relative">
        <div className="flex items-center justify-center gap-2 mb-4">
          <Sparkles className="w-5 h-5" style={{ color: "var(--violet)" }} />
          <span
            className="text-xs font-mono tracking-[0.3em] uppercase"
            style={{ color: "var(--violet)" }}
          >
            Rizz Verdict
          </span>
        </div>

        <p
          className="text-2xl md:text-3xl font-semibold leading-tight"
          style={{ color: "var(--text)" }}
        >
          &ldquo;{verdict}&rdquo;
        </p>

        {aiVerdict && aiVerdict !== "AI verdict unavailable." && (
          <div className="mt-6 pt-4 border-t border-border">
            <p
              className="text-xs font-mono mb-2"
              style={{ color: "var(--violet)" }}
            >
              AI-POWERED VERDICT
            </p>
            <p
              className="text-sm italic"
              style={{ color: "var(--text-secondary)" }}
            >
              &ldquo;{aiVerdict}&rdquo;
            </p>
          </div>
        )}
      </div>
    </motion.div>
  );
}
