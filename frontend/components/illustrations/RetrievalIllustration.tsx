"use client";

/**
 * RetrievalIllustration — v2
 * ───────────────────────────
 * Concept: "Large Document → Semantic Search → Relevant Chunks"
 *
 * Three visual zones read left → right:
 *   LEFT   — page stack (3 layered document cards, terracotta header)
 *   CENTRE — floating search lens with query-text hint + AI sparkle
 *   RIGHT  — three result cards ranked by score (0.94, 0.87, 0.81)
 *            with RELEVANT badge, score, and text-line previews
 *
 * Arrows: terracotta dashed doc→lens, sage dashed lens→each card
 * viewBox: 460 × 290  (wider and taller — cards fully visible)
 */
export default function RetrievalIllustration() {
  const resultCards = [
    { y: 24,  score: "0.94", lineW: [76, 62, 70], highlight: true  },
    { y: 110, score: "0.87", lineW: [68, 56, 64], highlight: false },
    { y: 196, score: "0.81", lineW: [72, 60, 58], highlight: false },
  ];

  return (
    <div
      className="relative w-full max-w-[460px] mx-auto select-none"
      aria-hidden="true"
    >
      <svg
        viewBox="0 0 460 290"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        className="w-full h-auto"
      >
        {/* ── Soft background blob ─────────────────────────────── */}
        <ellipse cx="230" cy="145" rx="215" ry="130" fill="#EFF2EB" opacity="0.45" />

        {/* ── Dot grid ─────────────────────────────────────────── */}
        {Array.from({ length: 6 }).map((_, r) =>
          Array.from({ length: 9 }).map((_, c) => (
            <circle key={`g-${r}-${c}`} cx={16 + c * 50} cy={16 + r * 50} r="1.3" fill="#D8C7B1" opacity="0.45" />
          ))
        )}

        {/* ════════════════════════════════════════════════════════
            LEFT — Document page stack
        ════════════════════════════════════════════════════════ */}

        {/* Page 3 — far back */}
        <rect
          x="12" y="62" width="92" height="128" rx="8"
          fill="#D8C7B1" opacity="0.45"
          transform="rotate(-5, 58, 126)"
        />
        {/* Page 2 — mid */}
        <rect
          x="16" y="56" width="92" height="128" rx="8"
          fill="#E4DBCF" opacity="0.70"
          transform="rotate(3, 62, 120)"
        />
        {/* Page 1 — front */}
        <rect x="20" y="50" width="92" height="128" rx="8"
          fill="#FBF8F2" stroke="#D8C7B1" strokeWidth="1.2" />
        {/* Header bar */}
        <rect x="20" y="50" width="92" height="24" rx="8" fill="#B9684E" opacity="0.88" />
        <rect x="20" y="63"  width="92" height="11" fill="#B9684E" opacity="0.88" />
        <text x="33" y="66" fontSize="7" fill="#FBF8F2" fontWeight="700" letterSpacing="0.6">STUDY NOTES</text>

        {/* Highlighted lines (key passages) */}
        <rect x="30" y="84"  width="72" height="5.5" rx="2.75" fill="#B9684E" opacity="0.18" />
        <rect x="30" y="84"  width="44" height="5.5" rx="2.75" fill="#87977B" opacity="0.28" />
        <rect x="30" y="95"  width="72" height="4"   rx="2"    fill="#7A6A5E" opacity="0.28" />
        <rect x="30" y="104" width="60" height="4"   rx="2"    fill="#7A6A5E" opacity="0.24" />
        <rect x="30" y="113" width="72" height="4"   rx="2"    fill="#B9684E" opacity="0.22" />
        <rect x="30" y="122" width="52" height="4"   rx="2"    fill="#7A6A5E" opacity="0.22" />
        <rect x="30" y="131" width="66" height="4"   rx="2"    fill="#87977B" opacity="0.30" />
        <rect x="30" y="140" width="46" height="4"   rx="2"    fill="#7A6A5E" opacity="0.22" />
        <rect x="30" y="153" width="72" height="4"   rx="2"    fill="#7A6A5E" opacity="0.20" />
        <rect x="30" y="162" width="56" height="4"   rx="2"    fill="#87977B" opacity="0.25" />

        {/* ════════════════════════════════════════════════════════
            ARROW 1: document → search lens
        ════════════════════════════════════════════════════════ */}
        <path
          d="M116 114 C132 114 148 114 162 114"
          stroke="#B9684E"
          strokeWidth="1.8"
          strokeDasharray="5 3.5"
          fill="none"
          markerEnd="url(#arrTC)"
        />

        {/* ════════════════════════════════════════════════════════
            CENTRE — Search lens (floating)
        ════════════════════════════════════════════════════════ */}
        <g
          className="animate-float"
          style={{ transformOrigin: "202px 114px" }}
        >
          {/* Outer glow ring */}
          <circle cx="202" cy="114" r="46" fill="#EFF2EB" opacity="0.7" />
          {/* Outer lens ring */}
          <circle cx="202" cy="114" r="38" fill="#FBF8F2" stroke="#87977B" strokeWidth="2" />
          {/* Inner lens ring */}
          <circle cx="202" cy="114" r="26" fill="none" stroke="#87977B" strokeWidth="2.5" />

          {/* Query text hint inside lens */}
          <rect x="184" y="108" width="36" height="4" rx="2" fill="#87977B" opacity="0.35" />
          <rect x="188" y="115" width="28" height="3" rx="1.5" fill="#87977B" opacity="0.22" />

          {/* AI sparkle dots inside */}
          <circle cx="194" cy="104" r="3.5" fill="#B9684E" opacity="0.45" />
          <circle cx="210" cy="120" r="2.5" fill="#B9684E" opacity="0.30" />

          {/* Lens handle */}
          <line
            x1="222" y1="134"
            x2="236" y2="148"
            stroke="#87977B"
            strokeWidth="3.5"
            strokeLinecap="round"
          />
        </g>

        {/* "SEARCH" label beneath lens */}
        <text
          x="202" y="170"
          fontSize="7"
          fill="#87977B"
          fontWeight="700"
          letterSpacing="0.8"
          textAnchor="middle"
        >
          SEMANTIC SEARCH
        </text>

        {/* ════════════════════════════════════════════════════════
            ARROWS 2-4: lens → each result card
        ════════════════════════════════════════════════════════ */}
        {/* → top card */}
        <path
          d="M240 100 C262 82 286 70 318 60"
          stroke="#87977B"
          strokeWidth="1.6"
          strokeDasharray="5 3.5"
          fill="none"
          markerEnd="url(#arrSG)"
        />
        {/* → middle card */}
        <path
          d="M242 114 C268 114 294 114 318 145"
          stroke="#87977B"
          strokeWidth="1.6"
          strokeDasharray="5 3.5"
          fill="none"
          markerEnd="url(#arrSG)"
        />
        {/* → bottom card */}
        <path
          d="M240 128 C262 148 286 164 318 198"
          stroke="#87977B"
          strokeWidth="1.4"
          strokeDasharray="5 3.5"
          fill="none"
          markerEnd="url(#arrSG)"
          opacity="0.75"
        />

        {/* ════════════════════════════════════════════════════════
            RIGHT — Result cards (3 ranked chunks)
        ════════════════════════════════════════════════════════ */}
        {resultCards.map((card, idx) => (
          <g key={idx} transform={`translate(318, ${card.y})`}>
            {/* Card shadow */}
            <rect
              width="130" height="72" rx="8"
              fill="#40352F" opacity="0.05"
              transform="translate(2,3)"
            />
            {/* Card body */}
            <rect
              width="130" height="72" rx="8"
              fill={card.highlight ? "#EFF2EB" : "#FBF8F2"}
              stroke={card.highlight ? "#87977B" : "#D8C7B1"}
              strokeWidth={card.highlight ? 1.5 : 1}
            />

            {/* Header row */}
            <rect x="0" y="0" width="130" height="22" rx="8"
              fill={card.highlight ? "#87977B" : "#D8C7B1"}
              opacity={card.highlight ? 0.18 : 0.22}
            />
            <rect x="0" y="14" width="130" height="8"
              fill={card.highlight ? "#87977B" : "#D8C7B1"}
              opacity={card.highlight ? 0.18 : 0.22}
            />

            {/* RELEVANT badge */}
            <rect x="8" y="5" width="44" height="12" rx="6"
              fill={card.highlight ? "#87977B" : "#D8C7B1"}
              opacity="0.25"
            />
            <text x="14" y="14.5" fontSize="6" fill={card.highlight ? "#87977B" : "#7A6A5E"} fontWeight="700" letterSpacing="0.4">
              RELEVANT
            </text>

            {/* Score */}
            <text
              x="122" y="14.5"
              fontSize="8"
              fill="#B9684E"
              fontWeight="700"
              textAnchor="end"
            >
              {card.score}
            </text>

            {/* Text preview lines */}
            {card.lineW.map((w, li) => (
              <rect
                key={li}
                x="8"
                y={30 + li * 12}
                width={w}
                height="4"
                rx="2"
                fill="#7A6A5E"
                opacity={0.38 - li * 0.06}
              />
            ))}

            {/* Rank number */}
            <text
              x="121" y="68"
              fontSize="7"
              fill={card.highlight ? "#87977B" : "#D8C7B1"}
              fontWeight="700"
              textAnchor="end"
            >
              #{idx + 1}
            </text>
          </g>
        ))}

        {/* ════════════════════════════════════════════════════════
            BOTTOM — Stage labels
        ════════════════════════════════════════════════════════ */}
        {[
          { x: 66,  label: "Document",  color: "#B9684E" },
          { x: 202, label: "AI Search", color: "#87977B" },
          { x: 383, label: "Results",   color: "#40352F" },
        ].map((s) => (
          <g key={s.label} transform={`translate(${s.x}, 265)`}>
            <circle cx="0" cy="0" r="3" fill={s.color} opacity="0.7" />
            <text x="0" y="14" fontSize="8" fill={s.color} fontWeight="600"
              letterSpacing="0.4" textAnchor="middle">
              {s.label}
            </text>
          </g>
        ))}

        {/* ── Arrow markers ────────────────────────────────────── */}
        <defs>
          <marker id="arrTC" markerWidth="7" markerHeight="7" refX="6" refY="3.5" orient="auto">
            <path d="M0,0.5 L6,3.5 L0,6.5 Z" fill="#B9684E" />
          </marker>
          <marker id="arrSG" markerWidth="7" markerHeight="7" refX="6" refY="3.5" orient="auto">
            <path d="M0,0.5 L6,3.5 L0,6.5 Z" fill="#87977B" />
          </marker>
        </defs>
      </svg>
    </div>
  );
}
