export type ScoreStatus = "strong" | "good" | "fair" | "weak";

export type ConfidenceLevel = "high" | "medium" | "low";

export interface Finding {
  id: string;
  severity: "critical" | "warning" | "info" | "positive";
  category: string;
  title: string;
  description: string;
  evidence?: string[];
  filePath?: string;
  recommendation?: string;
}

export interface DimensionScore {
  id: string;
  name: string;
  score: number;
  maxScore: number;
  weight: number;
  status: ScoreStatus;
  confidence: ConfidenceLevel;
  confidenceReason: string;
  findings: Finding[];
  evidence: string[];
  summary: string;
  recommendation: string;
  rawMetrics: Record<string, number | boolean | string | string[]>;
  rulesApplied: string[];
  limitations: string[];
}

/** The 5 primary user-facing dimensions */
export type PrimaryDimensionId =
  | "documentation"
  | "codeQuality"
  | "architecture"
  | "security"
  | "resumeReadiness";

/** Resume readiness status — distinct from ScoreStatus */
export type ResumeReadinessStatus = "ready" | "almostReady" | "needsWork" | "notReady";

export function getResumeReadinessStatus(score: number): ResumeReadinessStatus {
  if (score >= 80) return "ready";
  if (score >= 60) return "almostReady";
  if (score >= 40) return "needsWork";
  return "notReady";
}

export function getResumeReadinessLabel(status: ResumeReadinessStatus): string {
  switch (status) {
    case "ready": return "READY";
    case "almostReady": return "ALMOST READY";
    case "needsWork": return "NEEDS WORK";
    case "notReady": return "NOT READY";
  }
}

export function getResumeReadinessColor(status: ResumeReadinessStatus): string {
  switch (status) {
    case "ready": return "var(--lime)";
    case "almostReady": return "var(--blue)";
    case "needsWork": return "var(--coral)";
    case "notReady": return "var(--coral)";
  }
}

export interface AnalysisResult {
  id: string;
  repository: RepositoryInfo;
  /** The Resume Readiness score — the primary product metric */
  resumeReadinessScore: number;
  resumeReadinessStatus: ResumeReadinessStatus;
  resumeReadinessSummary: string;
  resumeReadinessStrengths: string[];
  resumeReadinessWeaknesses: string[];
  resumeReadinessBeforeResume: string[];
  /** The 4 engineering dimensions (without Resume Readiness) */
  engineeringDimensions: DimensionScore[];
  /** Resume Readiness as a full dimension with evidence */
  resumeReadinessDimension: DimensionScore;
  /** Combined array for backward compatibility */
  dimensions: DimensionScore[];
  rizzVerdict: string;
  criticalFindings: Finding[];
  recommendations: Recommendation[];
  aiSummary?: string;
  aiRizzVerdict?: string;
  aiUnavailable: boolean;
  analyzedAt: string;
  analysisTimeMs: number;
  limitations: string[];
  repositoryType?: {
    type: string;
    confidence: number;
    reason: string;
    signals: string[];
  };
  applicableDimensions?: number;
  notApplicableDimensions?: number;
  scoringVersion?: string;
  weightedContributions?: {
    dimension: string;
    score: number;
    effectiveWeight: number;
    contribution: number;
    applicable: boolean;
  }[];
}

export interface RepositoryInfo {
  owner: string;
  name: string;
  fullName: string;
  description: string | null;
  url: string;
  defaultBranch: string;
  stars: number;
  forks: number;
  watchers: number;
  openIssues: number;
  language: string | null;
  languages: Record<string, number>;
  createdAt: string;
  updatedAt: string;
  pushedAt: string;
  topics: string[];
  license: string | null;
  hasWiki: boolean;
  hasPages: boolean;
  size: number;
}

export interface ResumeReadiness {
  score: number;
  status: ScoreStatus;
  strengths: string[];
  weaknesses: string[];
  beforeYouPutThisOnResume: string[];
}

export interface Recommendation {
  id: string;
  priority: "critical" | "high" | "medium" | "low";
  category: string;
  title: string;
  description: string;
  impact: string;
}

export interface AnalysisPipeline {
  steps: PipelineStep[];
  status: "running" | "completed" | "partial" | "error";
}

export interface PipelineStep {
  id: string;
  order: number;
  label: string;
  status: "pending" | "running" | "completed" | "error" | "skipped";
  detail?: string;
  startedAt?: string;
  completedAt?: string;
}

export interface AnalysisRequest {
  owner: string;
  name: string;
}

export interface CompareRequest {
  repo1: { owner: string; name: string };
  repo2: { owner: string; name: string };
}

/** Only 5 primary dimensions — equal 20% weights */
export interface ScoreWeights {
  codeQuality: number;
  security: number;
  documentation: number;
  architecture: number;
  resumeReadiness: number;
}

export const DEFAULT_WEIGHTS: ScoreWeights = {
  codeQuality: 20,
  security: 20,
  documentation: 20,
  architecture: 20,
  resumeReadiness: 20,
};

export const PRIMARY_DIMENSION_IDS: PrimaryDimensionId[] = [
  "documentation",
  "codeQuality",
  "architecture",
  "security",
  "resumeReadiness",
];

export const ENGINEERING_DIMENSION_IDS = [
  "documentation",
  "codeQuality",
  "architecture",
  "security",
] as const;

export const DIMENSION_COLORS: Record<string, string> = {
  codeQuality: "#B6FF42",
  security: "#FF6848",
  documentation: "#5EA7FF",
  architecture: "#B6FF42",
  resumeReadiness: "#B6FF42",
};
