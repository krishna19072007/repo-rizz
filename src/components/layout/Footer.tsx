"use client";

import Link from "next/link";

export function Footer() {
  return (
    <footer className="border-t border-border mt-auto py-8" style={{ background: "var(--bg)" }}>
      <div className="max-w-7xl mx-auto px-6 flex flex-col md:flex-row justify-between items-center gap-4">
        
        <div className="flex flex-col items-center md:items-start text-center md:text-left">
          <span className="text-lg font-bold tracking-tight" style={{ color: "var(--text)" }}>
            REPO <span style={{ color: "var(--lime)" }}>RIZZ</span>
          </span>
          <p className="text-xs mt-1" style={{ color: "var(--text-secondary)" }}>
            Advanced GitHub repository analysis for developers.
          </p>
        </div>

        <div className="flex items-center gap-6">
          <Link 
            href="/about" 
            className="text-sm transition-colors hover:text-lime" 
            style={{ color: "var(--text-secondary)" }}
          >
            About
          </Link>
          
          <button 
            className="text-sm cursor-not-allowed transition-opacity hover:opacity-70" 
            style={{ color: "var(--text-secondary)" }} 
            title="Privacy Policy — Coming Soon"
            onClick={() => alert("Privacy Policy — Coming Soon")}
          >
            Privacy Policy
          </button>
          
          <a 
            href="https://github.com/krishna19072007/repo-rizz" 
            target="_blank" 
            rel="noopener noreferrer" 
            className="text-sm transition-colors hover:text-lime" 
            style={{ color: "var(--text-secondary)" }}
          >
            GitHub
          </a>
        </div>

      </div>
    </footer>
  );
}
