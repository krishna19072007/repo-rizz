import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatNumber(num: number): string {
  if (num >= 1_000_000) return `${(num / 1_000_000).toFixed(1)}M`;
  if (num >= 1_000) return `${(num / 1_000).toFixed(1)}K`;
  return num.toString();
}

export function formatDate(date: string | Date): string {
  return new Intl.DateTimeFormat("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  }).format(new Date(date));
}

export function timeAgo(date: string | Date): string {
  const now = new Date();
  const then = new Date(date);
  const seconds = Math.floor((now.getTime() - then.getTime()) / 1000);

  if (seconds < 60) return "just now";
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
  if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`;
  if (seconds < 2592000) return `${Math.floor(seconds / 86400)}d ago`;
  if (seconds < 31536000) return `${Math.floor(seconds / 2592000)}mo ago`;
  return `${Math.floor(seconds / 31536000)}y ago`;
}

export function scoreToColor(score: number): string {
  if (score >= 80) return "var(--lime)";
  if (score >= 60) return "var(--blue)";
  if (score >= 40) return "var(--violet)";
  return "var(--coral)";
}

export function scoreToLabel(score: number): string {
  if (score >= 80) return "STRONG";
  if (score >= 60) return "GOOD";
  if (score >= 40) return "FAIR";
  return "WEAK";
}

export function scoreToStatus(score: number): "strong" | "good" | "fair" | "weak" {
  if (score >= 80) return "strong";
  if (score >= 60) return "good";
  if (score >= 40) return "fair";
  return "weak";
}

export function getConfidence(level: string): string {
  switch (level) {
    case "high": return "HIGH CONFIDENCE";
    case "medium": return "MEDIUM CONFIDENCE";
    case "low": return "LOW CONFIDENCE";
    default: return "MEDIUM CONFIDENCE";
  }
}
