"use client";

import { useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import { ArrowRight, Zap, AlertCircle } from "lucide-react";
import { parseGitHubUrl } from "@/lib/validators";
import { cn } from "@/lib/utils";

interface RepoInputProps {
  variant?: "hero" | "compact";
  className?: string;
}

export function RepoInput({ variant = "hero", className }: RepoInputProps) {
  const [value, setValue] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isFocused, setIsFocused] = useState(false);
  const router = useRouter();

  const handleSubmit = useCallback(
    (e: React.FormEvent, demo?: boolean) => {
      e.preventDefault();

      if (demo) {
        router.push("/analyze?repo=krishna19072007/repo-rizz");
        return;
      }

      const parsed = parseGitHubUrl(value);
      if (!parsed) {
        setError("That doesn't look like a valid public GitHub repository.");
        return;
      }

      setError(null);
      router.push(`/analyze?repo=${parsed.owner}/${parsed.name}`);
    },
    [value, router]
  );

  const isHero = variant === "hero";

  return (
    <div className={cn("w-full", className)}>
      <form onSubmit={handleSubmit} className="relative">
        <div
          className={cn(
            "relative flex items-center rounded-2xl border transition-all duration-300",
            isHero ? "px-6 py-4" : "px-4 py-3",
            isFocused
              ? "border-lime/40 shadow-[0_0_20px_rgba(182,255,66,0.08)]"
              : "border-border hover:border-border-strong",
            error ? "border-coral/50" : ""
          )}
          style={{ background: "var(--surface)" }}
        >
          
          <input
            type="text"
            value={value}
            onChange={(e) => {
              setValue(e.target.value);
              setError(null);
            }}
            onFocus={() => setIsFocused(true)}
            onBlur={() => setIsFocused(false)}
            placeholder={isFocused ? "" : "ENTER GITHUB REPO LINK HERE..."}
            className={cn(
              "flex-1 bg-transparent outline-none placeholder:text-text-secondary/40 font-mono",
              isHero ? "text-lg" : "text-sm"
            )}
            style={{ color: "var(--text)" }}
            aria-label="GitHub repository URL"
            aria-invalid={!!error}
          />

          <button
            type="submit"
            className={cn(
              "flex items-center gap-2 rounded-xl font-semibold transition-all duration-200",
              "hover:scale-[1.02] active:scale-[0.98]",
              isHero
                ? "px-6 py-3 ml-3 text-sm"
                : "px-4 py-2 ml-2 text-xs"
            )}
            style={{
              background: "var(--lime)",
              color: "var(--bg)",
            }}
          >
            ANALYZE
            <ArrowRight className="w-4 h-4" />
          </button>
        </div>

        {error && (
          <div className="flex items-center gap-2 mt-3 text-sm" style={{ color: "var(--coral)" }}>
            <AlertCircle className="w-4 h-4 flex-shrink-0" />
            <span>{error}</span>
          </div>
        )}
      </form>

      {isHero && (
        <div className="flex flex-col sm:flex-row items-center justify-between mt-6 gap-4">
          <div className="flex items-center gap-4 text-xs text-text-secondary">
            <span>PUBLIC REPOSITORIES ONLY</span>
            <span className="w-1 h-1 rounded-full bg-border-strong" />
            <span>FREE ANALYSIS</span>
            <span className="w-1 h-1 rounded-full bg-border-strong" />
            <span>AI-ASSISTED</span>
          </div>

          <button
            onClick={(e) => handleSubmit(e as React.FormEvent, true)}
            className={cn(
              "flex items-center gap-2 text-xs font-medium transition-colors",
              "text-text-secondary hover:text-lime"
            )}
          >
            <Zap className="w-3 h-3" />
            TRY REPO RIZZ &rarr;
          </button>
        </div>
      )}
    </div>
  );
}



