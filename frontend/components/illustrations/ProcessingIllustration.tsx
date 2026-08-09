"use client";

/**
 * ProcessingIllustration — v2
 * ────────────────────────────
 * Concept: a horizontal pipeline read left-to-right:
 *
 *   [Document]  ──→  [Chunks]  ──→  [Embeddings]  ──→  [Qdrant]
 *
 * Each stage is a distinct visual object:
 *   • Document   — cream card with terracotta header + text lines
 *   • Chunks     — two stacked mini-cards with CHUNK labels
 *   • Embeddings — dot-cluster with sage connecting lines
 *   • Qdrant     — properly layered 3-D cylinder in sage/dark-brown
 *
 * Flow arrows are long enough to read clearly.
 * Stage labels sit below with colour-coded dots.
 * Pulsing dot animation on the embedding nodes communicates "processing".
 *
 * viewBox: 460 × 220  (wider + taller than v1's 380×160)
 */

export default function ProcessingIllustration() {
  /* Embedding dot positions */
  const dots = [
    { cx: 248, cy: 80,  r: 6,   fill: "#B9684E", delay: "0.0s" },
    { cx: 268, cy: 66,  r: 5,   fill: "#87977B", delay: "0.3s" },
    { cx: 280, cy: 92,  r: 5,   fill: "#40352F", delay: "0.6s" },
    { cx: 264, cy: 108, r: 4,   fill: "#87977B", delay: "0.9s" },
    { cx: 244, cy: 104, r: 4,   fill: "#C4CEBC", delay: "0.4s" },
    { cx: 290, cy: 76,  r: 3.5, fill: "#B9684E", delay: "0.7s" },
    { cx: 284, cy: 108, r: 3,   fill: "#D8C7B1", delay: "1.1s" },
  ];

  const dotEdges = [
    [0, 1], [1, 2], [2, 3], [3, 4], [4, 0], [1, 5], [2, 6],
  ] as const;

  return (
    <div
      className="relative w-full max-w-[460px] mx-auto select-none"
      aria-hidden="true"
    >
      <svg
        viewBox="0 0 460 220"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        className="w-full h-auto"
      >
        {/* ── Background blob ────────────────────────────────────── */}
        <ellipse cx="230" cy="110" rx="218" ry="98" fill="#EFF2EB" opacity="0.45" />

        {/* ── Subtle dot grid ─────────────────────────────────────── */}
        {Array.from({ length: 5 }).map((_, r) =>
          Array.from({ length: 10 }).map((_, c) => (
            <circle
              key={`g-${r}-${c}`}
              cx={18 + c * 46}
              cy={18 + r * 46}
              r="1.2"
              fill="#D8C7B1"
              opacity="0.4"
            />
          ))
        )}

        {/* ════════════════════════════════════════════════════════
            STAGE 1 — Document
        ════════════════════════════════════════════════════════ */}
        {/* Drop shadow */}
        <rect x="18" y="28" width="82" height="110" rx="8"
          fill="#40352F" opacity="0.06" transform="translate(2,3)" />
        {/* Card */}
        <rect x="18" y="28" width="82" height="110" rx="8" fill="#FBF8F2" stroke="#D8C7B1" strokeWidth="1" />
        {/* Header */}
        <rect x="18" y="28" width="82" height="22" rx="8" fill="#B9684E" opacity="0.9" />
        <rect x="18" y="41"  width="82" height="9"  fill="#B9684E" opacity="0.9" />
        <text x="30" y="43" fontSize="7" fill="#FBF8F2" fontWeight="700" letterSpacing="0.6">DOCUMENT</text>
        {/* Text lines */}
        <rect x="28" y="60" width="62" height="4" rx="2" fill="#40352F" opacity="0.6" />
        <rect x="28" y="70" width="54" height="3.5" rx="1.75" fill="#7A6A5E" opacity="0.35" />
        <rect x="28" y="79" width="58" height="3.5" rx="1.75" fill="#7A6A5E" opacity="0.30" />
        <rect x="28" y="88" width="46" height="3.5" rx="1.75" fill="#7A6A5E" opacity="0.25" />
        <rect x="28" y="100" width="62" height="3.5" rx="1.75" fill="#87977B" opacity="0.45" />
        <rect x="28" y="109" width="50" height="3.5" rx="1.75" fill="#7A6A5E" opacity="0.25" />
        {/* Corner fold */}
        <path d="M87 28 L100 28 L87 41 Z" fill="#D8C7B1" opacity="0.9" />

        {/* ════════════════════════════════════════════════════════
            ARROW 1
        ════════════════════════════════════════════════════════ */}
        <path
          d="M104 83 L126 83"
          stroke="#B9684E"
          strokeWidth="1.8"
          strokeDasharray="5 3"
          markerEnd="url(#arrowTC)"
        />

        {/* ════════════════════════════════════════════════════════
            STAGE 2 — Chunks (two stacked cards)
        ════════════════════════════════════════════════════════ */}
        {/* Chunk card A */}
        <rect x="130" y="42" width="72" height="38" rx="6" fill="#FBF8F2" stroke="#D8C7B1" strokeWidth="1" />
        <rect x="130" y="42" width="72" height="14" rx="6" fill="#B9684E" opacity="0.12" />
        <rect x="130" y="49" width="72" height="7" fill="#B9684E" opacity="0.12" />
        <text x="140" y="53" fontSize="5.5" fill="#B9684E" fontWeight="700" letterSpacing="0.3">CHUNK 01</text>
        <rect x="140" y="63" width="54" height="3" rx="1.5" fill="#7A6A5E" opacity="0.35" />
        <rect x="140" y="70" width="42" height="3" rx="1.5" fill="#7A6A5E" opacity="0.28" />

        {/* Chunk card B */}
        <rect x="130" y="92" width="72" height="38" rx="6" fill="#FBF8F2" stroke="#D8C7B1" strokeWidth="1" />
        <rect x="130" y="92" width="72" height="14" rx="6" fill="#B9684E" opacity="0.12" />
        <rect x="130" y="99" width="72" height="7"  fill="#B9684E" opacity="0.12" />
        <text x="140" y="103" fontSize="5.5" fill="#B9684E" fontWeight="700" letterSpacing="0.3">CHUNK 02</text>
        <rect x="140" y="113" width="48" height="3" rx="1.5" fill="#7A6A5E" opacity="0.35" />
        <rect x="140" y="120" width="58" height="3" rx="1.5" fill="#7A6A5E" opacity="0.28" />

        {/* ════════════════════════════════════════════════════════
            ARROW 2
        ════════════════════════════════════════════════════════ */}
        <path
          d="M206 83 L228 83"
          stroke="#87977B"
          strokeWidth="1.8"
          strokeDasharray="5 3"
          markerEnd="url(#arrowSG)"
        />

        {/* ════════════════════════════════════════════════════════
            STAGE 3 — Embeddings (dot cluster)
        ════════════════════════════════════════════════════════ */}
        {/* Soft enclosure */}
        <ellipse cx="268" cy="88" rx="46" ry="40" fill="#EFF2EB" opacity="0.8" />

        {/* Connection lines (drawn under dots) */}
        {dotEdges.map(([a, b], i) => (
          <line
            key={`e-${i}`}
            x1={dots[a].cx} y1={dots[a].cy}
            x2={dots[b].cx} y2={dots[b].cy}
            stroke="#C4CEBC"
            strokeWidth="1"
            opacity="0.7"
          />
        ))}

        {/* Dots with pulse animation */}
        {dots.map((d, i) => (
          <circle
            key={`dot-${i}`}
            cx={d.cx}
            cy={d.cy}
            r={d.r}
            fill={d.fill}
            opacity="0.85"
            style={{ animation: `pulseDot 2.4s ease-in-out infinite`, animationDelay: d.delay }}
          />
        ))}

        {/* VECTORS label */}
        <text
          x="268" y="136"
          fontSize="6"
          fill="#87977B"
          fontWeight="700"
          letterSpacing="0.6"
          textAnchor="middle"
        >
          VECTORS
        </text>

        {/* ════════════════════════════════════════════════════════
            ARROW 3
        ════════════════════════════════════════════════════════ */}
        <path
          d="M318 83 L340 83"
          stroke="#40352F"
          strokeWidth="1.8"
          strokeDasharray="5 3"
          markerEnd="url(#arrowDB)"
          opacity="0.5"
        />

        {/* ════════════════════════════════════════════════════════
            STAGE 4 — Qdrant cylinder (properly layered)
        ════════════════════════════════════════════════════════ */}

        {/* Cylinder side — drawn as a rect between the two ellipses */}
        <rect x="318" y="55" width="66" height="58" fill="#87977B" opacity="0.75" />

        {/* Cylinder bottom ellipse */}
        <ellipse cx="351" cy="113" rx="33" ry="10" fill="#87977B" opacity="0.6" />

        {/* Cylinder top ellipse (drawn last so it sits on top) */}
        <ellipse cx="351" cy="55" rx="33" ry="10" fill="#87977B" opacity="0.95" />

        {/* Stripe lines */}
        <line x1="318" y1="72"  x2="384" y2="72"  stroke="#FBF8F2" strokeWidth="0.8" opacity="0.35" />
        <line x1="318" y1="87"  x2="384" y2="87"  stroke="#FBF8F2" strokeWidth="0.8" opacity="0.35" />
        <line x1="318" y1="102" x2="384" y2="102" stroke="#FBF8F2" strokeWidth="0.8" opacity="0.35" />

        {/* QDRANT label centered on cylinder face */}
        <text
          x="351" y="88"
          fontSize="8"
          fill="#FBF8F2"
          fontWeight="700"
          letterSpacing="0.8"
          textAnchor="middle"
        >
          QDRANT
        </text>

        {/* ════════════════════════════════════════════════════════
            STAGE LABELS — bottom row with colour-coded dots
        ════════════════════════════════════════════════════════ */}
        {[
          { x: 59,  label: "Document",   color: "#B9684E" },
          { x: 166, label: "Chunks",     color: "#B9684E" },
          { x: 268, label: "Embeddings", color: "#87977B" },
          { x: 351, label: "Qdrant",     color: "#40352F" },
        ].map((s) => (
          <g key={s.label} transform={`translate(${s.x}, 155)`}>
            <circle cx="0" cy="0" r="3.5" fill={s.color} opacity="0.8" />
            <text
              x="0" y="14"
              fontSize="7.5"
              fill={s.color}
              fontWeight="600"
              letterSpacing="0.3"
              textAnchor="middle"
            >
              {s.label}
            </text>
          </g>
        ))}

        {/* ════════════════════════════════════════════════════════
            ARROW MARKERS
        ════════════════════════════════════════════════════════ */}
        <defs>
          <marker id="arrowTC" markerWidth="7" markerHeight="7" refX="6" refY="3.5" orient="auto">
            <path d="M0,0.5 L6,3.5 L0,6.5 Z" fill="#B9684E" />
          </marker>
          <marker id="arrowSG" markerWidth="7" markerHeight="7" refX="6" refY="3.5" orient="auto">
            <path d="M0,0.5 L6,3.5 L0,6.5 Z" fill="#87977B" />
          </marker>
          <marker id="arrowDB" markerWidth="7" markerHeight="7" refX="6" refY="3.5" orient="auto">
            <path d="M0,0.5 L6,3.5 L0,6.5 Z" fill="#40352F" opacity="0.5" />
          </marker>
        </defs>

        {/* ── Inline keyframe for dot pulse ─ */}
        <style>{`
          @keyframes pulseDot {
            0%, 100% { opacity: 0.85; r: var(--r); }
            50%       { opacity: 0.45; }
          }
        `}</style>
      </svg>
    </div>
  );
}
