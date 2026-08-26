"use client";

import { motion } from "framer-motion";
import Link from "next/link";
import { Clock, ArrowRight } from "lucide-react";

export default function HistoryPage() {
  return (
    <div
      className="min-h-screen pt-24 pb-32 px-6"
      style={{ background: "var(--bg)" }}
    >
      <div className="max-w-4xl mx-auto">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center mb-16"
        >
          <Link
            href="/"
            className="text-xs font-mono mb-8 inline-block transition-colors hover:text-lime"
            style={{ color: "var(--text-secondary)" }}
          >
            ← Back to Home
          </Link>

          <h1
            className="text-4xl md:text-5xl font-bold tracking-tight mb-4"
            style={{ color: "var(--text)" }}
          >
            ANALYSIS <span style={{ color: "var(--lime)" }}>HISTORY</span>
          </h1>
          <p
            className="text-sm max-w-lg mx-auto"
            style={{ color: "var(--text-secondary)" }}
          >
            View your past repository analyses and track improvements over time.
          </p>
        </motion.div>

        {/* Empty state */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="text-center py-20"
        >
          <Clock
            className="w-12 h-12 mx-auto mb-4"
            style={{ color: "var(--text-secondary)", opacity: 0.3 }}
          />
          <h2
            className="text-xl font-semibold mb-2"
            style={{ color: "var(--text)" }}
          >
            No analyses yet
          </h2>
          <p
            className="text-sm mb-8"
            style={{ color: "var(--text-secondary)" }}
          >
            Analyze a repository to see it appear here.
          </p>
          <Link
            href="/analyze"
            className="inline-flex items-center gap-2 px-6 py-3 rounded-xl font-semibold text-sm transition-all hover:scale-[1.02]"
            style={{ background: "var(--lime)", color: "var(--bg)" }}
          >
            Start Analyzing
            <ArrowRight className="w-4 h-4" />
          </Link>
        </motion.div>
      </div>
    </div>
  );
}
