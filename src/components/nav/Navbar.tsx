"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";

const navLinks = [
  { href: "/", label: "Home" },
  { href: "/analyze", label: "Analyze" },
  { href: "/compare", label: "Compare" },
  { href: "/history", label: "History" },
];

export function Navbar() {
  const pathname = usePathname();

  return (
    <nav
      className="fixed top-0 left-0 right-0 z-50 border-b border-border"
      style={{ background: "rgba(7, 8, 9, 0.85)", backdropFilter: "blur(12px)" }}
    >
      <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
        <Link href="/" className="flex items-center gap-3 group">
          <div
            className="w-8 h-8 rounded-lg flex items-center justify-center text-sm font-bold"
            style={{ background: "var(--lime)", color: "var(--bg)" }}
          >
            R
          </div>
          <span className="text-lg font-semibold tracking-tight" style={{ color: "var(--text)" }}>
            REPO <span style={{ color: "var(--lime)" }}>RIZZ</span>
          </span>
        </Link>

        <div className="hidden md:flex items-center gap-1">
          {navLinks.map((link) => (
            <Link
              key={link.href}
              href={link.href}
              className={cn(
                "px-4 py-2 rounded-lg text-sm font-medium transition-colors",
                pathname === link.href
                  ? "bg-surface-elevated text-lime"
                  : "text-text-secondary hover:text-text hover:bg-surface"
              )}
            >
              {link.label}
            </Link>
          ))}
        </div>

        <div className="flex items-center gap-3">
          <a
            href="https://github.com"
            target="_blank"
            rel="noopener noreferrer"
            className="text-text-secondary hover:text-text text-sm transition-colors"
          >
            GitHub
          </a>
        </div>
      </div>
    </nav>
  );
}
