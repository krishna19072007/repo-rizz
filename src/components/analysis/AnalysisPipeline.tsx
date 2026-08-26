"use client";

import { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Check, Loader2, AlertCircle, ChevronRight } from "lucide-react";
import { cn } from "@/lib/utils";

interface PipelineStep {
  id: string;
  order: number;
  label: string;
  status: "pending" | "running" | "completed" | "error" | "skipped";
}

const PIPELINE_STEPS: Omit<PipelineStep, "status">[] = [
  { id: "fetch", order: 1, label: "FETCHING REPOSITORY" },
  { id: "metadata", order: 2, label: "READING METADATA" },
  { id: "tree", order: 3, label: "INSPECTING FILE TREE" },
  { id: "docs", order: 4, label: "ANALYZING DOCUMENTATION" },
  { id: "activity", order: 5, label: "ANALYZING ACTIVITY" },
  { id: "cicd", order: 6, label: "INSPECTING CI/CD" },
  { id: "security", order: 7, label: "CHECKING SECURITY SIGNALS" },
  { id: "deps", order: 8, label: "ANALYZING DEPENDENCIES" },
  { id: "health", order: 9, label: "CALCULATING HEALTH" },
  { id: "insights", order: 10, label: "GENERATING INSIGHTS" },
];

interface AnalysisPipelineProps {
  owner: string;
  name: string;
  onComplete?: () => void;
}

export function AnalysisPipeline({ owner, name, onComplete }: AnalysisPipelineProps) {
  const [steps, setSteps] = useState<PipelineStep[]>(
    PIPELINE_STEPS.map((s) => ({ ...s, status: "pending" }))
  );
  const [currentStep, setCurrentStep] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [isPartial, setIsPartial] = useState(false);

  useEffect(() => {
    // Simulate pipeline progression while actual analysis runs
    const interval = setInterval(() => {
      setCurrentStep((prev) => {
        if (prev >= PIPELINE_STEPS.length - 1) {
          clearInterval(interval);
          return prev;
        }
        return prev + 1;
      });
    }, 400);

    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    setSteps((prev) =>
      prev.map((step, i) => {
        if (i < currentStep) return { ...step, status: "completed" as const };
        if (i === currentStep) return { ...step, status: "running" as const };
        return { ...step, status: "pending" as const };
      })
    );
  }, [currentStep]);

  // Call onComplete when all steps are done
  useEffect(() => {
    if (currentStep >= PIPELINE_STEPS.length - 1) {
      const timer = setTimeout(() => {
        onComplete?.();
      }, 800);
      return () => clearTimeout(timer);
    }
  }, [currentStep, onComplete]);

  return (
    <div className="w-full max-w-2xl mx-auto">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
        className="text-center mb-10"
      >
        <p
          className="text-xs font-mono tracking-[0.3em] mb-3"
          style={{ color: "var(--text-secondary)" }}
        >
          REPO RIZZ ANALYSIS
        </p>
        <p className="text-2xl font-semibold" style={{ color: "var(--text)" }}>
          {owner}/<span style={{ color: "var(--lime)" }}>{name}</span>
        </p>
      </motion.div>

      <div className="space-y-1">
        <AnimatePresence>
          {steps.map((step, i) => (
            <motion.div
              key={step.id}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: i * 0.05, duration: 0.3 }}
              className={cn(
                "flex items-center gap-3 px-4 py-3 rounded-lg transition-colors",
                step.status === "running" && "bg-surface-elevated",
                step.status === "completed" && "opacity-60"
              )}
            >
              <div className="w-6 h-6 flex items-center justify-center flex-shrink-0">
                {step.status === "completed" && (
                  <Check className="w-4 h-4" style={{ color: "var(--lime)" }} />
                )}
                {step.status === "running" && (
                  <Loader2
                    className="w-4 h-4 animate-spin"
                    style={{ color: "var(--lime)" }}
                  />
                )}
                {step.status === "error" && (
                  <AlertCircle className="w-4 h-4" style={{ color: "var(--coral)" }} />
                )}
                {step.status === "pending" && (
                  <span className="text-xs font-mono" style={{ color: "var(--text-secondary)" }}>
                    {String(step.order).padStart(2, "0")}
                  </span>
                )}
              </div>

              <span
                className={cn(
                  "text-sm font-mono tracking-wide",
                  step.status === "running" && "font-semibold"
                )}
                style={{
                  color:
                    step.status === "running"
                      ? "var(--lime)"
                      : step.status === "completed"
                      ? "var(--text-secondary)"
                      : step.status === "error"
                      ? "var(--coral)"
                      : "var(--text-secondary)",
                }}
              >
                {step.label}
              </span>

              {step.status === "running" && (
                <motion.div
                  className="ml-auto"
                  animate={{ opacity: [0.5, 1, 0.5] }}
                  transition={{ duration: 1.5, repeat: Infinity }}
                >
                  <ChevronRight className="w-4 h-4" style={{ color: "var(--lime)" }} />
                </motion.div>
              )}
            </motion.div>
          ))}
        </AnimatePresence>
      </div>

      {(error || isPartial) && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="mt-6 text-center"
        >
          <p className="text-sm" style={{ color: "var(--coral)" }}>
            {error || "PARTIAL ANALYSIS — Some data could not be fetched"}
          </p>
        </motion.div>
      )}
    </div>
  );
}
