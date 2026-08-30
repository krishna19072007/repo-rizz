"use client";

import { useState } from "react";
import Link from "next/link";
import Image from "next/image";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import { BrandModal } from "@/components/modals/BrandModal";

const navLinks = [
  { href: "/", label: "Home" },
  { href: "/analyze", label: "Repo's Rizz" },
  { href: "/compare", label: "Repo Battle" },
  { href: "/history", label: "History" },
];

export function Navbar() {
  const pathname = usePathname();
  const [isBrandModalOpen, setIsBrandModalOpen] = useState(false);

  return (
    <>
      <nav
        className="fixed top-0 left-0 right-0 z-50 border-b border-border"
        style={{ background: "rgba(7, 8, 9, 0.85)", backdropFilter: "blur(12px)" }}
      >
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <button 
              onClick={() => setIsBrandModalOpen(true)}
              className="relative w-8 h-8 focus:outline-none focus:ring-2 focus:ring-lime rounded-sm transition-transform hover:scale-105"
              aria-label="About Repo Rizz"
            >
              <Image 
                src="/logo.png" 
                alt="Repo Rizz Logo"
                fill
                className="object-contain"
              />
            </button>
            <Link href="/" className="flex items-center">
              <span className="text-lg font-semibold tracking-tight hover:opacity-80 transition-opacity" style={{ color: "var(--text)" }}>
                REPO <span style={{ color: "var(--lime)" }}>RIZZ</span>
              </span>
            </Link>
          </div>

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
              href="https://github.com/krishna19072007/repo-rizz"
              target="_blank"
              rel="noopener noreferrer"
              className="text-text-secondary hover:text-text text-sm transition-colors"
            >
              GitHub
            </a>
          </div>
        </div>
      </nav>

      <BrandModal 
        isOpen={isBrandModalOpen} 
        onClose={() => setIsBrandModalOpen(false)} 
      />
    </>
  );
}
