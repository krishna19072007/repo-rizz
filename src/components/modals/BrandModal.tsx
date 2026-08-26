"use client";

import { useEffect } from "react";
import Image from "next/image";
import { motion, AnimatePresence } from "framer-motion";
import { X } from "lucide-react";

interface BrandModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export function BrandModal({ isOpen, onClose }: BrandModalProps) {
  // Handle escape key
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        onClose();
      }
    };
    
    if (isOpen) {
      window.addEventListener("keydown", handleKeyDown);
    }
    
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isOpen, onClose]);

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            className="fixed inset-0 z-[100]"
            style={{ 
              background: "rgba(0, 0, 0, 0.7)", 
              backdropFilter: "blur(8px)" 
            }}
          />

          {/* Modal Container */}
          <div className="fixed inset-0 z-[101] flex items-center justify-center pointer-events-none p-4">
            <motion.div
              initial={{ opacity: 0, scale: 0.95, y: 10 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95, y: 10 }}
              transition={{ type: "spring", damping: 25, stiffness: 300 }}
              className="relative w-full max-w-md rounded-2xl pointer-events-auto overflow-hidden border border-border"
              style={{ background: "var(--surface)", boxShadow: "0 25px 50px -12px rgba(0, 0, 0, 0.5)" }}
            >
              {/* Close button */}
              <button
                onClick={onClose}
                className="absolute top-4 right-4 p-2 rounded-full text-text-secondary hover:text-text hover:bg-surface-elevated transition-colors z-10"
                aria-label="Close"
              >
                <X size={20} />
              </button>

              <div className="p-10 flex flex-col items-center justify-center text-center">
                <div className="relative w-40 h-40 mb-6 drop-shadow-2xl">
                  <Image 
                    src="/logo.png" 
                    alt="Repo Rizz Logo" 
                    fill 
                    className="object-contain"
                    priority
                  />
                </div>
                
                <h2 className="text-3xl font-bold tracking-tight mb-2" style={{ color: "var(--text)" }}>
                  REPO <span style={{ color: "var(--lime)" }}>RIZZ</span>
                </h2>
                
                <p className="text-sm" style={{ color: "var(--text-secondary)" }}>
                  AI-powered GitHub repository analysis and scoring engine.
                </p>
                
                <div className="mt-8 pt-6 w-full border-t border-border flex justify-center space-x-6">
                  <a href="https://github.com/krishna19072007/repo-rizz" target="_blank" rel="noopener noreferrer" className="text-xs font-mono tracking-wider hover:text-lime transition-colors" style={{ color: "var(--text-secondary)" }}>
                    SOURCE CODE
                  </a>
                  <a href="#" className="text-xs font-mono tracking-wider hover:text-lime transition-colors" style={{ color: "var(--text-secondary)" }}>
                    DOCUMENTATION
                  </a>
                </div>
              </div>
            </motion.div>
          </div>
        </>
      )}
    </AnimatePresence>
  );
}
