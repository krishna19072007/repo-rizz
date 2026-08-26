"use client";

import { useRef, Suspense } from "react";
import { motion, useScroll, useTransform } from "framer-motion";
import { RepoInput } from "@/components/hero/RepoInput";
import { RepoFingerprint } from "@/components/three/RepoFingerprint";
import { ArrowDown } from "lucide-react";

const DIMENSIONS = [
  { name: "Code", color: "var(--lime)" },
  { name: "Security", color: "var(--coral)" },
  { name: "Docs", color: "var(--blue)" },
  { name: "Tests", color: "var(--violet)" },
  { name: "Architecture", color: "var(--lime)" },
  { name: "Maintainability", color: "var(--blue)" },
  { name: "Activity", color: "var(--violet)" },
  { name: "Community", color: "var(--coral)" },
  { name: "Resume", color: "var(--lime)" },
];

const PIPELINE_STEPS = [
  "FETCH",
  "INSPECT",
  "ANALYZE",
  "VERIFY",
  "SCORE",
  "EXPLAIN",
  "IMPROVE",
];

export default function HomePage() {
  return (
    <main className="min-h-screen" style={{ background: "var(--bg)" }}>
      <HeroSection />
      <DimensionScroll />
      <PipelineSection />
      <FinalCTA />
    </main>
  );
}

function HeroSection() {
  const ref = useRef<HTMLDivElement>(null);

  return (
    <section
      ref={ref}
      className="relative min-h-screen flex items-center justify-center overflow-hidden grid-pattern"
    >
      {/* 3D Background */}
      <div className="absolute inset-0 opacity-40 pointer-events-none">
        <Suspense fallback={null}>
          <RepoFingerprint className="absolute inset-0" />
        </Suspense>
      </div>

      {/* Gradient overlays */}
      <div
        className="absolute inset-0 pointer-events-none"
        style={{
          background:
            "radial-gradient(ellipse at 50% 30%, rgba(182, 255, 66, 0.04) 0%, transparent 60%)",
        }}
      />

      <div className="relative z-10 max-w-5xl mx-auto px-6 text-center">
        {/* Main headline */}
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, ease: "easeOut" }}
        >
          <p
            className="text-xs font-mono tracking-[0.4em] mb-8"
            style={{ color: "var(--text-secondary)" }}
          >
            ENGINEERING HEALTH ANALYSIS
          </p>

          <h1
            className="text-6xl md:text-8xl lg:text-9xl font-bold leading-[0.9] tracking-tight mb-8"
            style={{ color: "var(--text)" }}
          >
            YOUR REPO
            <br />
            HAS A
            <br />
            <span style={{ color: "var(--lime)" }}>REPUTATION</span>.
          </h1>
        </motion.div>

        <motion.p
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.3, duration: 0.6 }}
          className="text-lg md:text-xl max-w-2xl mx-auto mb-4"
          style={{ color: "var(--text-secondary)" }}
        >
          Repo Rizz turns a GitHub repository into an engineering health report.
        </motion.p>

        <motion.p
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.4, duration: 0.6 }}
          className="text-sm mb-12 font-mono"
          style={{ color: "var(--text-secondary)", opacity: 0.6 }}
        >
          Code quality · Security · Documentation · Testing · Maintainability · Activity · Architecture · Resume readiness
        </motion.p>

        {/* Input */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.5, duration: 0.6 }}
          className="max-w-2xl mx-auto"
        >
          <RepoInput variant="hero" />
        </motion.div>

        {/* Examples */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.7 }}
          className="mt-8 flex flex-wrap items-center justify-center gap-3 text-xs font-mono"
          style={{ color: "var(--text-secondary)" }}
        >
          <span style={{ opacity: 0.5 }}>TRY:</span>
          {["vercel/next.js", "facebook/react", "microsoft/vscode"].map((repo) => (
            <span
              key={repo}
              className="px-3 py-1 rounded-lg border border-border cursor-pointer hover:border-border-strong transition-colors"
              style={{ background: "var(--surface)" }}
            >
              {repo}
            </span>
          ))}
        </motion.div>

        {/* Scroll indicator */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 1.2 }}
          className="mt-16"
        >
          <motion.div
            animate={{ y: [0, 8, 0] }}
            transition={{ duration: 2, repeat: Infinity }}
            className="inline-flex flex-col items-center gap-2"
          >
            <span className="text-[10px] font-mono" style={{ color: "var(--text-secondary)" }}>
              SCROLL TO EXPLORE
            </span>
            <ArrowDown className="w-4 h-4" style={{ color: "var(--text-secondary)" }} />
          </motion.div>
        </motion.div>
      </div>
    </section>
  );
}

function DimensionScroll() {
  const containerRef = useRef<HTMLDivElement>(null);
  const { scrollYProgress } = useScroll({
    target: containerRef,
    offset: ["start end", "end start"],
  });

  return (
    <section
      ref={containerRef}
      className="py-32 px-6"
      style={{ background: "var(--bg)" }}
    >
      <div className="max-w-5xl mx-auto">
        {/* Section intro */}
        <motion.div
          initial={{ opacity: 0, y: 40 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: "-100px" }}
          transition={{ duration: 0.8 }}
          className="text-center mb-24"
        >
          <h2
            className="text-4xl md:text-6xl font-bold tracking-tight mb-6"
            style={{ color: "var(--text)" }}
          >
            IT&apos;S MORE THAN
            <br />
            <span style={{ color: "var(--text-secondary)" }}>&ldquo;DOES IT RUN?&rdquo;</span>
          </h2>
        </motion.div>

        {/* Dimension typography */}
        <div className="space-y-8">
          {DIMENSIONS.map((dim, i) => (
            <motion.div
              key={dim.name}
              initial={{ opacity: 0, x: i % 2 === 0 ? -60 : 60 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true, margin: "-50px" }}
              transition={{ duration: 0.6, delay: 0.1 }}
              className="text-center"
            >
              <span
                className="text-5xl md:text-7xl lg:text-8xl font-bold tracking-tight"
                style={{
                  color: dim.color,
                  opacity: 0.9,
                }}
              >
                {dim.name}
              </span>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}

function PipelineSection() {
  return (
    <section className="py-32 px-6" style={{ background: "var(--surface)" }}>
      <div className="max-w-4xl mx-auto text-center">
        <motion.div
          initial={{ opacity: 0, y: 40 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.8 }}
        >
          <p
            className="text-xs font-mono tracking-[0.3em] mb-4"
            style={{ color: "var(--violet)" }}
          >
            THE PROCESS
          </p>
          <h2
            className="text-3xl md:text-5xl font-bold tracking-tight mb-16"
            style={{ color: "var(--text)" }}
          >
            SHOW HOW REPO RIZZ THINKS
          </h2>
        </motion.div>

        {/* Pipeline visualization */}
        <div className="space-y-4">
          {PIPELINE_STEPS.map((step, i) => (
            <motion.div
              key={step}
              initial={{ opacity: 0, x: -20 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true }}
              transition={{ delay: i * 0.1, duration: 0.4 }}
              className="flex items-center justify-center gap-4"
            >
              <div
                className="text-2xl md:text-4xl font-bold font-mono tracking-wider"
                style={{
                  color: i === PIPELINE_STEPS.length - 1 ? "var(--lime)" : "var(--text)",
                }}
              >
                {step}
              </div>
              {i < PIPELINE_STEPS.length - 1 && (
                <span className="text-lg" style={{ color: "var(--text-secondary)" }}>
                  ↓
                </span>
              )}
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}

function FinalCTA() {
  return (
    <section className="py-32 px-6" style={{ background: "var(--bg)" }}>
      <div className="max-w-3xl mx-auto text-center">
        <motion.div
          initial={{ opacity: 0, y: 40 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.8 }}
        >
          <h2
            className="text-4xl md:text-6xl font-bold tracking-tight mb-8"
            style={{ color: "var(--text)" }}
          >
            READY TO CHECK YOUR
            <br />
            <span style={{ color: "var(--lime)" }}>REPO&apos;S RIZZ</span>?
          </h2>

          <p
            className="text-lg mb-12"
            style={{ color: "var(--text-secondary)" }}
          >
            Paste a GitHub repository URL and get a full engineering health report in seconds.
          </p>

          <RepoInput variant="compact" />
        </motion.div>
      </div>
    </section>
  );
}
