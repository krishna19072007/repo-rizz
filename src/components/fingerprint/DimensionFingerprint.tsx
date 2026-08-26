"use client";

import { useMemo, useRef, useState, useEffect } from "react";
import { motion } from "framer-motion";
import { DimensionScore } from "@/lib/types";
import { cn, scoreToColor } from "@/lib/utils";

interface DimensionFingerprintProps {
  dimensions: DimensionScore[];
  className?: string;
}

/** Only the 4 engineering dimensions appear on the radar */
const RADAR_DIMENSION_IDS = ["documentation", "codeQuality", "architecture", "security"];

/**
 * The radar uses a virtual SVG coordinate system of 500x500.
 * The radar shape occupies the inner 320x320 area.
 * Labels occupy the outer ring (320→500), with 90px of space on each side.
 * The container scales to fit any width via viewBox + width:100%.
 */
const VIRTUAL_W = 540;
const VIRTUAL_H = 500;
const RADAR_CX = VIRTUAL_W / 2;
const RADAR_CY = VIRTUAL_H / 2;
const RADAR_RADIUS = 125;
const LABEL_RADIUS = RADAR_RADIUS + 42;

export function DimensionFingerprint({
  dimensions,
  className,
}: DimensionFingerprintProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [width, setWidth] = useState(400);

  useEffect(() => {
    if (!containerRef.current) return;
    const observer = new ResizeObserver((entries) => {
      for (const entry of entries) {
        setWidth(entry.contentRect.width);
      }
    });
    observer.observe(containerRef.current);
    return () => observer.disconnect();
  }, []);

  const radarDimensions = useMemo(() => {
    return RADAR_DIMENSION_IDS
      .map(id => dimensions.find(d => d.id === id))
      .filter(Boolean) as DimensionScore[];
  }, [dimensions]);

  const angleStep = (Math.PI * 2) / Math.max(1, radarDimensions.length);

  const points = useMemo(() => {
    return radarDimensions.map((dim, i) => {
      const angle = i * angleStep - Math.PI / 2;
      const score = dim.score / 100;
      const radius = RADAR_RADIUS * score;

      return {
        x: RADAR_CX + Math.cos(angle) * radius,
        y: RADAR_CY + Math.sin(angle) * radius,
        labelX: RADAR_CX + Math.cos(angle) * LABEL_RADIUS,
        labelY: RADAR_CY + Math.sin(angle) * LABEL_RADIUS,
        innerX: RADAR_CX + Math.cos(angle) * RADAR_RADIUS,
        innerY: RADAR_CY + Math.sin(angle) * RADAR_RADIUS,
        textAnchor: Math.abs(Math.cos(angle)) < 0.1
          ? "middle"
          : Math.cos(angle) > 0
            ? "start"
            : "end",
        angle,
        dim,
        score,
      };
    });
  }, [radarDimensions, angleStep]);

  const polygonPath = useMemo(() => {
    if (points.length === 0) return "";
    return points.map((p, i) => `${i === 0 ? "M" : "L"} ${p.x} ${p.y}`).join(" ") + " Z";
  }, [points]);

  const gridPaths = useMemo(() => {
    return [0.25, 0.5, 0.75, 1].map((s) => {
      return points
        .map((p, i) => {
          const x = RADAR_CX + Math.cos(p.angle) * RADAR_RADIUS * s;
          const y = RADAR_CY + Math.sin(p.angle) * RADAR_RADIUS * s;
          return `${i === 0 ? "M" : "L"} ${x} ${y}`;
        })
        .join(" ") + " Z";
    });
  }, [points]);

  return (
    <div
      ref={containerRef}
      className={cn("w-full", className)}
      style={{ maxWidth: 540 }}
    >
      <svg
        width="100%"
        viewBox={`0 0 ${VIRTUAL_W} ${VIRTUAL_H}`}
        xmlns="http://www.w3.org/2000/svg"
      >
        {/* Grid rings */}
        {gridPaths.map((path, i) => (
          <path key={i} d={path} fill="none" stroke="rgba(255,255,255,0.05)" strokeWidth={1} />
        ))}

        {/* Axis lines */}
        {points.map((p, i) => (
          <line
            key={`axis-${i}`}
            x1={RADAR_CX} y1={RADAR_CY}
            x2={p.innerX} y2={p.innerY}
            stroke="rgba(255,255,255,0.05)" strokeWidth={1}
          />
        ))}

        {/* Score polygon */}
        <motion.path
          d={polygonPath}
          fill="rgba(182, 255, 66, 0.08)"
          stroke="var(--lime)"
          strokeWidth={2}
          initial={{ pathLength: 0, opacity: 0 }}
          animate={{ pathLength: 1, opacity: 1 }}
          transition={{ duration: 1.5, ease: "easeOut" }}
        />

        {/* Score dots */}
        {points.map((p, i) => (
          <motion.g key={`dot-${i}`}>
            <motion.circle
              cx={p.x} cy={p.y} r={5}
              fill={scoreToColor(p.dim.score)}
              initial={{ scale: 0 }} animate={{ scale: 1 }}
              transition={{ delay: 0.1 * i, duration: 0.3 }}
            />
            <motion.circle
              cx={p.x} cy={p.y} r={10}
              fill={scoreToColor(p.dim.score)} opacity={0.15}
              initial={{ scale: 0 }} animate={{ scale: 1 }}
              transition={{ delay: 0.1 * i + 0.1, duration: 0.4 }}
            />
          </motion.g>
        ))}

        {/* Labels — SVG text, scales with viewBox, never clipped */}
        {points.map((p, i) => (
          <text
            key={`label-${i}`}
            x={p.labelX}
            y={p.labelY}
            textAnchor={p.textAnchor as "start" | "end" | "middle"}
            dominantBaseline="middle"
            fill="var(--text-secondary)"
            fontSize={13}
            fontFamily="var(--font-mono)"
          >
            {p.dim.name}
          </text>
        ))}

        {/* Center label */}
        <text
          x={RADAR_CX} y={RADAR_CY - 5}
          textAnchor="middle" dominantBaseline="middle"
          fill="var(--text)" fontSize={13} fontWeight="bold"
          fontFamily="var(--font-mono)"
        >
          4
        </text>
        <text
          x={RADAR_CX} y={RADAR_CY + 9}
          textAnchor="middle" dominantBaseline="middle"
          fill="var(--text-secondary)" fontSize={8}
          fontFamily="var(--font-mono)"
        >
          DIMENSIONS
        </text>
      </svg>
    </div>
  );
}
