"use client";

import { useRef, useMemo, useCallback, useEffect, useState } from "react";
import { Canvas, useFrame, useThree } from "@react-three/fiber";
import * as THREE from "three";

function ParticleField({ count = 200 }: { count?: number }) {
  const mesh = useRef<THREE.Points>(null!);
  const mouseRef = useRef({ x: 0, y: 0 });

  const [positions, colors, sizes] = useMemo(() => {
    const pos = new Float32Array(count * 3);
    const col = new Float32Array(count * 3);
    const sz = new Float32Array(count);

    const limeColor = new THREE.Color("#B6FF42");
    const violetColor = new THREE.Color("#7C5CFF");
    const coralColor = new THREE.Color("#FF6848");
    const blueColor = new THREE.Color("#5EA7FF");
    const accentColors = [limeColor, violetColor, coralColor, blueColor];

    for (let i = 0; i < count; i++) {
      // Create a fingerprint-like distribution
      const angle = (i / count) * Math.PI * 6 + Math.random() * 0.5;
      const radius = 0.3 + (i / count) * 2.5 + Math.random() * 0.3;
      const height = (Math.random() - 0.5) * 3;

      pos[i * 3] = Math.cos(angle) * radius;
      pos[i * 3 + 1] = height;
      pos[i * 3 + 2] = Math.sin(angle) * radius;

      const color = accentColors[Math.floor(Math.random() * accentColors.length)];
      col[i * 3] = color.r;
      col[i * 3 + 1] = color.g;
      col[i * 3 + 2] = color.b;

      sz[i] = Math.random() * 3 + 1;
    }

    return [pos, col, sz];
  }, [count]);

  const { camera } = useThree();

  const handlePointerMove = useCallback((e: PointerEvent) => {
    mouseRef.current.x = (e.clientX / window.innerWidth) * 2 - 1;
    mouseRef.current.y = -(e.clientY / window.innerHeight) * 2 + 1;
  }, []);

  useEffect(() => {
    window.addEventListener("pointermove", handlePointerMove);
    return () => window.removeEventListener("pointermove", handlePointerMove);
  }, [handlePointerMove]);

  useFrame((state) => {
    if (!mesh.current) return;
    const time = state.clock.elapsedTime;

    mesh.current.rotation.y = time * 0.05 + mouseRef.current.x * 0.1;
    mesh.current.rotation.x = Math.sin(time * 0.3) * 0.05 + mouseRef.current.y * 0.05;

    // Subtle floating
    mesh.current.position.y = Math.sin(time * 0.5) * 0.1;

    // Update camera based on mouse
    camera.position.x = THREE.MathUtils.lerp(
      camera.position.x,
      mouseRef.current.x * 0.3,
      0.02
    );
    camera.position.y = THREE.MathUtils.lerp(
      camera.position.y,
      mouseRef.current.y * 0.3 + 0.5,
      0.02
    );
    camera.lookAt(0, 0, 0);
  });

  return (
    <points ref={mesh}>
      <bufferGeometry>
        <bufferAttribute
          attach="attributes-position"
          args={[positions, 3]}
        />
        <bufferAttribute
          attach="attributes-color"
          args={[colors, 3]}
        />
        <bufferAttribute
          attach="attributes-size"
          args={[sizes, 1]}
        />
      </bufferGeometry>
      <pointsMaterial
        size={0.04}
        vertexColors
        transparent
        opacity={0.8}
        sizeAttenuation
        blending={THREE.AdditiveBlending}
        depthWrite={false}
      />
    </points>
  );
}

function ScoreLines() {
  const groupRef = useRef<THREE.Group>(null!);

  const lineGeometry = useMemo(() => {
    const points: THREE.Vector3[] = [];
    const dimensions = 9;

    for (let i = 0; i < dimensions; i++) {
      const angle1 = (i / dimensions) * Math.PI * 2;
      const angle2 = ((i + 1) / dimensions) * Math.PI * 2;

      const r = 2 + Math.random() * 0.5;
      points.push(
        new THREE.Vector3(Math.cos(angle1) * r, (Math.random() - 0.5) * 2, Math.sin(angle1) * r),
        new THREE.Vector3(Math.cos(angle2) * r, (Math.random() - 0.5) * 2, Math.sin(angle2) * r)
      );
    }

    const geometry = new THREE.BufferGeometry().setFromPoints(points);
    return geometry;
  }, []);

  useFrame((state) => {
    if (groupRef.current) {
      groupRef.current.rotation.y = state.clock.elapsedTime * 0.02;
    }
  });

  return (
    <group ref={groupRef}>
      <lineSegments geometry={lineGeometry}>
        <lineBasicMaterial color="#B6FF42" transparent opacity={0.15} />
      </lineSegments>
    </group>
  );
}

function GlowNodes() {
  const groupRef = useRef<THREE.Group>(null!);

  const nodes = useMemo(() => {
    return Array.from({ length: 9 }, (_, i) => {
      const angle = (i / 9) * Math.PI * 2;
      const r = 2.2;
      return {
        position: [Math.cos(angle) * r, (Math.random() - 0.5) * 1.5, Math.sin(angle) * r] as [number, number, number],
        color: ["#B6FF42", "#7C5CFF", "#FF6848", "#5EA7FF"][i % 4],
      };
    });
  }, []);

  useFrame((state) => {
    if (groupRef.current) {
      groupRef.current.rotation.y = state.clock.elapsedTime * 0.03;
    }
  });

  return (
    <group ref={groupRef}>
      {nodes.map((node, i) => (
        <mesh key={i} position={node.position}>
          <sphereGeometry args={[0.08, 16, 16]} />
          <meshBasicMaterial color={node.color} transparent opacity={0.6} />
        </mesh>
      ))}
    </group>
  );
}

export function RepoFingerprint({
  className,
  reducedMotion = false,
}: {
  className?: string;
  reducedMotion?: boolean;
}) {
  const [isMobile, setIsMobile] = useState(false);
  const [prefersReducedMotion, setPrefersReducedMotion] = useState(false);

  useEffect(() => {
    setIsMobile(window.innerWidth < 768);
    setPrefersReducedMotion(
      window.matchMedia("(prefers-reduced-motion: reduce)").matches
    );
  }, []);

  const shouldAnimate = !reducedMotion && !prefersReducedMotion;
  const particleCount = isMobile ? 80 : 200;

  return (
    <div className={className} style={{ width: "100%", height: "100%" }}>
      <Canvas
        camera={{ position: [0, 0.5, 5], fov: 50 }}
        dpr={[1, 1.5]}
        gl={{ antialias: true, alpha: true }}
        style={{ background: "transparent" }}
      >
        {shouldAnimate && (
          <>
            <ParticleField count={particleCount} />
            <ScoreLines />
            <GlowNodes />
          </>
        )}
      </Canvas>
    </div>
  );
}
