"use client";

/**
 * HeroIllustration
 * ─────────────────
 * Concept: "AI Knowledge Retrieval"
 * A floating study document, organised page stack, text-chunk blocks,
 * embedding-connection dots, a search lens, and a study-plan card —
 * all communicating the pipeline: document → knowledge → plan.
 *
 * Palette: Cream bg, Sage objects, Terracotta highlights, Dark-brown details.
 * No neon. No robot. Pure SVG, no external assets.
 */

export default function HeroIllustration() {
  return (
    <div className="relative w-full max-w-[540px] mx-auto select-none" aria-hidden="true">
      <svg
        viewBox="0 0 540 480"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        className="w-full h-auto"
      >
        {/* ── Soft background blob ───────────────────────────── */}
        <ellipse cx="270" cy="250" rx="230" ry="200" fill="#EFF2EB" opacity="0.6" />

        {/* ── Dot grid (background texture) ─────────────────── */}
        {Array.from({ length: 8 }).map((_, row) =>
          Array.from({ length: 10 }).map((_, col) => (
            <circle
              key={`dot-${row}-${col}`}
              cx={60 + col * 50}
              cy={60 + row * 50}
              r="1.5"
              fill="#D8C7B1"
              opacity="0.7"
            />
          ))
        )}

        {/* ══════════════════════════════════════════════════════
            LAYER 1 — Background page stack (three tilted pages)
        ══════════════════════════════════════════════════════ */}

        {/* Page 3 — far back, tilted right */}
        <g transform="rotate(8, 300, 220)">
          <rect x="220" y="100" width="130" height="168" rx="8" fill="#D8C7B1" opacity="0.5" />
          <rect x="232" y="118" width="80" height="6" rx="3" fill="#87977B" opacity="0.4" />
          <rect x="232" y="130" width="60" height="4" rx="2" fill="#87977B" opacity="0.3" />
          <rect x="232" y="140" width="70" height="4" rx="2" fill="#87977B" opacity="0.3" />
        </g>

        {/* Page 2 — mid, slightly tilted */}
        <g transform="rotate(-5, 280, 230)">
          <rect x="210" y="110" width="130" height="168" rx="8" fill="#E4DBCF" opacity="0.7" />
          <rect x="222" y="128" width="90" height="6" rx="3" fill="#87977B" opacity="0.5" />
          <rect x="222" y="140" width="65" height="4" rx="2" fill="#87977B" opacity="0.4" />
          <rect x="222" y="150" width="75" height="4" rx="2" fill="#87977B" opacity="0.4" />
          <rect x="222" y="160" width="55" height="4" rx="2" fill="#87977B" opacity="0.3" />
        </g>

        {/* ══════════════════════════════════════════════════════
            LAYER 2 — Main floating document (front-and-center)
        ══════════════════════════════════════════════════════ */}
        <g className="animate-float" style={{ transformOrigin: "275px 210px" }}>
          {/* Document shadow */}
          <rect x="168" y="92" width="148" height="192" rx="10" fill="#40352F" opacity="0.08" />
          {/* Document body */}
          <rect x="162" y="85" width="148" height="192" rx="10" fill="#FBF8F2" />
          {/* Document top-bar accent */}
          <rect x="162" y="85" width="148" height="28" rx="10" fill="#B9684E" />
          <rect x="162" y="98" width="148" height="15" fill="#B9684E" />
          {/* Top-bar label */}
          <text x="178" y="104" fontFamily="Georgia, serif" fontSize="10" fill="#FBF8F2" fontWeight="600" letterSpacing="0.5">STUDY NOTES</text>

          {/* Document heading line */}
          <rect x="178" y="126" width="100" height="7" rx="3.5" fill="#40352F" opacity="0.8" />

          {/* Text lines */}
          <rect x="178" y="142" width="112" height="4" rx="2" fill="#7A6A5E" opacity="0.5" />
          <rect x="178" y="152" width="95" height="4" rx="2" fill="#7A6A5E" opacity="0.4" />
          <rect x="178" y="162" width="104" height="4" rx="2" fill="#7A6A5E" opacity="0.4" />
          <rect x="178" y="172" width="80" height="4" rx="2" fill="#7A6A5E" opacity="0.3" />

          {/* Divider */}
          <rect x="178" y="186" width="112" height="1" fill="#D8C7B1" />

          {/* Section 2 */}
          <rect x="178" y="196" width="90" height="5" rx="2.5" fill="#40352F" opacity="0.6" />
          <rect x="178" y="208" width="108" height="4" rx="2" fill="#7A6A5E" opacity="0.4" />
          <rect x="178" y="218" width="88" height="4" rx="2" fill="#7A6A5E" opacity="0.35" />
          <rect x="178" y="228" width="100" height="4" rx="2" fill="#7A6A5E" opacity="0.35" />
          <rect x="178" y="238" width="72" height="4" rx="2" fill="#7A6A5E" opacity="0.3" />

          {/* Corner fold */}
          <path d="M292 85 L310 85 L292 103 Z" fill="#D8C7B1" opacity="0.8" />
          <path d="M292 103 L310 85" stroke="#C4CEBC" strokeWidth="0.8" />

          {/* Sparkle — top right */}
          <g transform="translate(300, 76)">
            <line x1="0" y1="-7" x2="0" y2="7" stroke="#B9684E" strokeWidth="1.5" strokeLinecap="round" />
            <line x1="-7" y1="0" x2="7" y2="0" stroke="#B9684E" strokeWidth="1.5" strokeLinecap="round" />
            <line x1="-5" y1="-5" x2="5" y2="5" stroke="#B9684E" strokeWidth="1" strokeLinecap="round" opacity="0.6" />
            <line x1="5" y1="-5" x2="-5" y2="5" stroke="#B9684E" strokeWidth="1" strokeLinecap="round" opacity="0.6" />
          </g>
        </g>

        {/* ══════════════════════════════════════════════════════
            LAYER 3 — Chunk blocks (left side, extracted pieces)
        ══════════════════════════════════════════════════════ */}

        {/* Chunk 1 */}
        <g transform="translate(52, 130)">
          <rect width="96" height="52" rx="8" fill="#FBF8F2" stroke="#D8C7B1" strokeWidth="1" />
          <rect x="10" y="12" width="60" height="4" rx="2" fill="#87977B" opacity="0.8" />
          <rect x="10" y="22" width="76" height="3" rx="1.5" fill="#7A6A5E" opacity="0.4" />
          <rect x="10" y="30" width="56" height="3" rx="1.5" fill="#7A6A5E" opacity="0.35" />
          <rect x="10" y="38" width="66" height="3" rx="1.5" fill="#7A6A5E" opacity="0.3" />
          {/* CHUNK label */}
          <rect x="10" y="4" width="32" height="5" rx="2.5" fill="#B9684E" opacity="0.15" />
          <text x="14" y="8" fontSize="4.5" fill="#B9684E" fontWeight="700" letterSpacing="0.3">CHUNK</text>
        </g>

        {/* Chunk 2 */}
        <g transform="translate(44, 200)">
          <rect width="96" height="52" rx="8" fill="#FBF8F2" stroke="#D8C7B1" strokeWidth="1" />
          <rect x="10" y="12" width="50" height="4" rx="2" fill="#87977B" opacity="0.8" />
          <rect x="10" y="22" width="70" height="3" rx="1.5" fill="#7A6A5E" opacity="0.4" />
          <rect x="10" y="30" width="60" height="3" rx="1.5" fill="#7A6A5E" opacity="0.35" />
          <rect x="10" y="38" width="50" height="3" rx="1.5" fill="#7A6A5E" opacity="0.3" />
          <rect x="10" y="4" width="32" height="5" rx="2.5" fill="#B9684E" opacity="0.15" />
          <text x="14" y="8" fontSize="4.5" fill="#B9684E" fontWeight="700" letterSpacing="0.3">CHUNK</text>
        </g>

        {/* Chunk 3 */}
        <g transform="translate(58, 268)">
          <rect width="96" height="52" rx="8" fill="#FBF8F2" stroke="#D8C7B1" strokeWidth="1" />
          <rect x="10" y="12" width="70" height="4" rx="2" fill="#87977B" opacity="0.8" />
          <rect x="10" y="22" width="76" height="3" rx="1.5" fill="#7A6A5E" opacity="0.4" />
          <rect x="10" y="30" width="55" height="3" rx="1.5" fill="#7A6A5E" opacity="0.3" />
          <rect x="10" y="4" width="32" height="5" rx="2.5" fill="#B9684E" opacity="0.15" />
          <text x="14" y="8" fontSize="4.5" fill="#B9684E" fontWeight="700" letterSpacing="0.3">CHUNK</text>
        </g>

        {/* ══════════════════════════════════════════════════════
            LAYER 4 — Connector lines (doc → chunks)
        ══════════════════════════════════════════════════════ */}
        <path d="M162 160 Q120 160 148 156" stroke="#D8C7B1" strokeWidth="1.5" strokeDasharray="4 3" fill="none" />
        <path d="M162 200 Q130 200 140 226" stroke="#D8C7B1" strokeWidth="1.5" strokeDasharray="4 3" fill="none" />
        <path d="M162 240 Q135 250 154 294" stroke="#D8C7B1" strokeWidth="1.5" strokeDasharray="4 3" fill="none" />

        {/* ══════════════════════════════════════════════════════
            LAYER 5 — Embedding dots cluster (center)
        ══════════════════════════════════════════════════════ */}
        {[
          { cx: 280, cy: 360, r: 5, fill: "#B9684E" },
          { cx: 310, cy: 350, r: 4, fill: "#87977B" },
          { cx: 298, cy: 380, r: 3.5, fill: "#40352F" },
          { cx: 260, cy: 375, r: 4, fill: "#87977B" },
          { cx: 325, cy: 370, r: 3, fill: "#B9684E" },
          { cx: 270, cy: 345, r: 3, fill: "#40352F" },
          { cx: 340, cy: 355, r: 2.5, fill: "#C4CEBC" },
          { cx: 250, cy: 360, r: 3, fill: "#D8C7B1" },
        ].map((d, i) => (
          <circle key={i} cx={d.cx} cy={d.cy} r={d.r} fill={d.fill} opacity="0.85" />
        ))}

        {/* Connecting lines between dots */}
        <line x1="280" y1="360" x2="310" y2="350" stroke="#C4CEBC" strokeWidth="1" opacity="0.7" />
        <line x1="280" y1="360" x2="298" y2="380" stroke="#C4CEBC" strokeWidth="1" opacity="0.7" />
        <line x1="280" y1="360" x2="260" y2="375" stroke="#C4CEBC" strokeWidth="1" opacity="0.7" />
        <line x1="310" y1="350" x2="325" y2="370" stroke="#C4CEBC" strokeWidth="1" opacity="0.6" />
        <line x1="298" y1="380" x2="325" y2="370" stroke="#C4CEBC" strokeWidth="1" opacity="0.6" />
        <line x1="270" y1="345" x2="280" y2="360" stroke="#C4CEBC" strokeWidth="1" opacity="0.5" />
        <line x1="260" y1="375" x2="298" y2="380" stroke="#C4CEBC" strokeWidth="1" opacity="0.5" />

        {/* Label */}
        <text x="270" y="415" fontSize="8" fill="#87977B" fontWeight="600" letterSpacing="0.5" textAnchor="middle">VECTOR EMBEDDINGS</text>

        {/* ══════════════════════════════════════════════════════
            LAYER 6 — Search lens (right side)
        ══════════════════════════════════════════════════════ */}
        <g transform="translate(390, 175)">
          <circle cx="22" cy="22" r="22" fill="#EFF2EB" stroke="#87977B" strokeWidth="2" />
          <circle cx="22" cy="22" r="14" fill="none" stroke="#87977B" strokeWidth="2.5" />
          <line x1="32" y1="32" x2="42" y2="42" stroke="#87977B" strokeWidth="3" strokeLinecap="round" />
          {/* sparkle inside lens */}
          <circle cx="18" cy="18" r="2.5" fill="#B9684E" opacity="0.6" />
          <circle cx="26" cy="25" r="1.5" fill="#B9684E" opacity="0.4" />
        </g>

        {/* ══════════════════════════════════════════════════════
            LAYER 7 — Study plan card (bottom right)
        ══════════════════════════════════════════════════════ */}
        <g transform="translate(368, 280)">
          <rect width="140" height="120" rx="10" fill="#FBF8F2" stroke="#D8C7B1" strokeWidth="1" />
          {/* Card header */}
          <rect width="140" height="26" rx="10" fill="#87977B" opacity="0.9" />
          <rect y="16" width="140" height="10" fill="#87977B" opacity="0.9" />
          <text x="14" y="17" fontSize="8" fill="#FBF8F2" fontWeight="700" letterSpacing="0.5">STUDY PLAN</text>

          {/* Day rows */}
          {[
            { y: 38, w: 80, label: "Day 1" },
            { y: 56, w: 68, label: "Day 2" },
            { y: 74, w: 74, label: "Day 3" },
            { y: 92, w: 58, label: "Day 4" },
          ].map((d) => (
            <g key={d.y}>
              <circle cx="18" cy={d.y + 2} r="3.5" fill="#B9684E" opacity="0.7" />
              <text x="28" y={d.y + 5} fontSize="6.5" fill="#40352F" opacity="0.7">{d.label}</text>
              <rect x="60" y={d.y - 2} width={d.w} height="5" rx="2.5" fill="#D8C7B1" opacity="0.7" />
            </g>
          ))}

          {/* AI sparkle on card */}
          <g transform="translate(118, 10)">
            <line x1="0" y1="-4" x2="0" y2="4" stroke="#FBF8F2" strokeWidth="1.2" strokeLinecap="round" />
            <line x1="-4" y1="0" x2="4" y2="0" stroke="#FBF8F2" strokeWidth="1.2" strokeLinecap="round" />
          </g>
        </g>

        {/* ══════════════════════════════════════════════════════
            LAYER 8 — Flow arrows (doc→search→plan)
        ══════════════════════════════════════════════════════ */}
        {/* Document → search lens */}
        <path d="M310 185 Q360 180 390 196" stroke="#B9684E" strokeWidth="1.5" strokeDasharray="5 3" fill="none" opacity="0.6" markerEnd="url(#arrowOrange)" />
        {/* Search → plan card */}
        <path d="M432 230 Q440 250 440 280" stroke="#87977B" strokeWidth="1.5" strokeDasharray="5 3" fill="none" opacity="0.6" markerEnd="url(#arrowSage)" />

        {/* Arrow markers */}
        <defs>
          <marker id="arrowOrange" markerWidth="6" markerHeight="6" refX="5" refY="3" orient="auto">
            <path d="M0,0 L6,3 L0,6 Z" fill="#B9684E" opacity="0.6" />
          </marker>
          <marker id="arrowSage" markerWidth="6" markerHeight="6" refX="5" refY="3" orient="auto">
            <path d="M0,0 L6,3 L0,6 Z" fill="#87977B" opacity="0.6" />
          </marker>
        </defs>

        {/* ══════════════════════════════════════════════════════
            LAYER 9 — Floating label pills
        ══════════════════════════════════════════════════════ */}
        {/* "PDF" pill on document */}
        <g transform="translate(162, 68)">
          <rect width="28" height="14" rx="7" fill="#B9684E" />
          <text x="6" y="10" fontSize="6.5" fill="#FBF8F2" fontWeight="700">PDF</text>
        </g>

        {/* "AI" badge near sparkle */}
        <g transform="translate(315, 56)">
          <rect width="26" height="14" rx="7" fill="#87977B" />
          <text x="7" y="10" fontSize="6.5" fill="#FBF8F2" fontWeight="700">AI</text>
        </g>
      </svg>
    </div>
  );
}
