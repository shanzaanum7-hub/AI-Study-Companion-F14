"use client";

/**
 * DocumentIllustration — v2
 * ─────────────────────────
 * Shown beside the upload card.
 * Concept: a main study-document floats above a tidy page stack; three
 * labelled "chunk" cards fan out to the right connected by dashed lines;
 * a fourth "embeddings" card shows a mini vector-dot cluster.
 * Format labels (PDF · TXT) appear as pill badges.
 *
 * Fully self-contained SVG — no external assets.
 * Palette: #FBF8F2 · #B9684E · #87977B · #D8C7B1 · #40352F · #EFF2EB
 */
export default function DocumentIllustration() {
  return (
    <div
      className="relative w-full max-w-[380px] mx-auto select-none"
      aria-hidden="true"
    >
      <svg
        viewBox="0 0 380 420"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        className="w-full h-auto drop-shadow-sm"
      >
        {/* ── Background blob ──────────────────────────────────── */}
        <ellipse cx="175" cy="210" rx="158" ry="185" fill="#EFF2EB" opacity="0.55" />

        {/* ── Dot grid texture ─────────────────────────────────── */}
        {Array.from({ length: 7 }).map((_, r) =>
          Array.from({ length: 7 }).map((_, c) => (
            <circle
              key={`d-${r}-${c}`}
              cx={22 + c * 44}
              cy={22 + r * 54}
              r="1.4"
              fill="#D8C7B1"
              opacity="0.5"
            />
          ))
        )}

        {/* ════════════════════════════════════════════════════════
            PAGE STACK — three tilted pages behind the main doc
        ════════════════════════════════════════════════════════ */}
        <g transform="rotate(7, 145, 210)">
          <rect x="56" y="64" width="162" height="212" rx="9" fill="#D8C7B1" opacity="0.45" />
        </g>
        <g transform="rotate(-4, 145, 210)">
          <rect x="60" y="60" width="162" height="212" rx="9" fill="#E4DBCF" opacity="0.65" />
          <rect x="76" y="84" width="90" height="5" rx="2.5" fill="#87977B" opacity="0.35" />
          <rect x="76" y="94" width="74" height="4" rx="2" fill="#87977B" opacity="0.25" />
        </g>

        {/* ════════════════════════════════════════════════════════
            MAIN DOCUMENT — front card, gently floating
        ════════════════════════════════════════════════════════ */}
        <g
          className="animate-float"
          style={{ transformOrigin: "145px 195px" }}
        >
          {/* Drop shadow */}
          <rect
            x="58" y="52" width="162" height="212" rx="11"
            fill="#40352F" opacity="0.07"
            transform="translate(4,6)"
          />
          {/* Card body */}
          <rect x="58" y="52" width="162" height="212" rx="11" fill="#FBF8F2" />

          {/* Header bar */}
          <rect x="58" y="52" width="162" height="34" rx="11" fill="#B9684E" />
          <rect x="58" y="68" width="162" height="18" fill="#B9684E" />

          {/* Header text */}
          <text
            x="76" y="73"
            fontSize="9.5"
            fill="#FBF8F2"
            fontWeight="700"
            letterSpacing="0.8"
            fontFamily="Georgia, serif"
          >
            STUDY NOTES
          </text>

          {/* PDF pill badge */}
          <rect x="76" y="96" width="30" height="14" rx="7" fill="#B9684E" />
          <text x="84" y="106.5" fontSize="7" fill="#FBF8F2" fontWeight="700">PDF</text>

          {/* TXT pill badge */}
          <rect x="113" y="96" width="30" height="14" rx="7" fill="#87977B" opacity="0.8" />
          <text x="120" y="106.5" fontSize="7" fill="#FBF8F2" fontWeight="700">TXT</text>

          {/* Section heading line */}
          <rect x="76" y="120" width="128" height="6" rx="3" fill="#40352F" opacity="0.75" />

          {/* Body text lines — alternating lengths */}
          {[
            { y: 134, w: 128, op: 0.40 },
            { y: 144, w: 108, op: 0.35 },
            { y: 154, w: 118, op: 0.35 },
            { y: 164, w: 90,  op: 0.30 },
          ].map((l) => (
            <rect key={l.y} x="76" y={l.y} width={l.w} height="4" rx="2" fill="#7A6A5E" opacity={l.op} />
          ))}

          {/* Highlighted line (sage = important concept) */}
          <rect x="76" y="178" width="128" height="5" rx="2.5" fill="#87977B" opacity="0.55" />

          {[
            { y: 192, w: 110, op: 0.35 },
            { y: 202, w: 96,  op: 0.30 },
            { y: 212, w: 120, op: 0.30 },
            { y: 222, w: 82,  op: 0.25 },
          ].map((l) => (
            <rect key={l.y} x="76" y={l.y} width={l.w} height="4" rx="2" fill="#7A6A5E" opacity={l.op} />
          ))}

          {/* Bottom section heading */}
          <rect x="76" y="238" width="100" height="5" rx="2.5" fill="#40352F" opacity="0.55" />

          {/* Corner fold */}
          <path d="M200 52 L220 52 L200 72 Z" fill="#D8C7B1" opacity="0.9" />
          <path d="M200 72 L220 52" stroke="#C4CEBC" strokeWidth="0.8" />

          {/* Sparkle */}
          <g transform="translate(234, 44)">
            <line x1="0" y1="-7" x2="0" y2="7"  stroke="#B9684E" strokeWidth="1.5" strokeLinecap="round" />
            <line x1="-7" y1="0" x2="7" y2="0"  stroke="#B9684E" strokeWidth="1.5" strokeLinecap="round" />
            <line x1="-4.5" y1="-4.5" x2="4.5" y2="4.5" stroke="#B9684E" strokeWidth="1" strokeLinecap="round" opacity="0.55" />
            <line x1="4.5" y1="-4.5" x2="-4.5" y2="4.5" stroke="#B9684E" strokeWidth="1" strokeLinecap="round" opacity="0.55" />
          </g>
        </g>

        {/* ════════════════════════════════════════════════════════
            DASHED CONNECTOR LINES — doc → chunk cards
        ════════════════════════════════════════════════════════ */}
        <path d="M220 132 C248 132 248 132 254 132" stroke="#D8C7B1" strokeWidth="1.4" strokeDasharray="4 3" fill="none" />
        <path d="M220 190 C238 190 242 196 254 200" stroke="#D8C7B1" strokeWidth="1.4" strokeDasharray="4 3" fill="none" />
        <path d="M220 240 C236 240 244 268 254 272" stroke="#D8C7B1" strokeWidth="1.4" strokeDasharray="4 3" fill="none" />
        <path d="M220 255 C236 260 244 324 254 336" stroke="#C4CEBC" strokeWidth="1.2" strokeDasharray="3 3" fill="none" opacity="0.7" />

        {/* ════════════════════════════════════════════════════════
            CHUNK CARDS — right column
        ════════════════════════════════════════════════════════ */}

        {/* Chunk 1 */}
        <g transform="translate(254, 108)">
          <rect width="108" height="52" rx="8" fill="#FBF8F2" stroke="#D8C7B1" strokeWidth="1.2" />
          {/* CHUNK pill */}
          <rect x="8" y="8" width="36" height="12" rx="6" fill="#B9684E" opacity="0.12" />
          <text x="12" y="17.5" fontSize="6" fill="#B9684E" fontWeight="700" letterSpacing="0.3">CHUNK 01</text>
          {/* Lines */}
          <rect x="8" y="25" width="90"  height="3.5" rx="1.75" fill="#7A6A5E" opacity="0.38" />
          <rect x="8" y="33" width="76"  height="3.5" rx="1.75" fill="#7A6A5E" opacity="0.30" />
          <rect x="8" y="41" width="82"  height="3.5" rx="1.75" fill="#7A6A5E" opacity="0.25" />
        </g>

        {/* Chunk 2 */}
        <g transform="translate(254, 176)">
          <rect width="108" height="52" rx="8" fill="#FBF8F2" stroke="#D8C7B1" strokeWidth="1.2" />
          <rect x="8" y="8" width="36" height="12" rx="6" fill="#B9684E" opacity="0.12" />
          <text x="12" y="17.5" fontSize="6" fill="#B9684E" fontWeight="700" letterSpacing="0.3">CHUNK 02</text>
          <rect x="8" y="25" width="84"  height="3.5" rx="1.75" fill="#7A6A5E" opacity="0.38" />
          <rect x="8" y="33" width="70"  height="3.5" rx="1.75" fill="#7A6A5E" opacity="0.30" />
          <rect x="8" y="41" width="90"  height="3.5" rx="1.75" fill="#7A6A5E" opacity="0.25" />
        </g>

        {/* Chunk 3 */}
        <g transform="translate(254, 244)">
          <rect width="108" height="52" rx="8" fill="#FBF8F2" stroke="#D8C7B1" strokeWidth="1.2" />
          <rect x="8" y="8" width="36" height="12" rx="6" fill="#B9684E" opacity="0.12" />
          <text x="12" y="17.5" fontSize="6" fill="#B9684E" fontWeight="700" letterSpacing="0.3">CHUNK 03</text>
          <rect x="8" y="25" width="88"  height="3.5" rx="1.75" fill="#7A6A5E" opacity="0.38" />
          <rect x="8" y="33" width="64"  height="3.5" rx="1.75" fill="#7A6A5E" opacity="0.30" />
          <rect x="8" y="41" width="78"  height="3.5" rx="1.75" fill="#7A6A5E" opacity="0.25" />
        </g>

        {/* Embeddings card */}
        <g transform="translate(254, 312)">
          <rect width="108" height="66" rx="8" fill="#EFF2EB" stroke="#87977B" strokeWidth="1.2" />
          {/* EMBEDDING pill */}
          <rect x="8" y="8" width="48" height="12" rx="6" fill="#87977B" opacity="0.20" />
          <text x="12" y="17.5" fontSize="6" fill="#87977B" fontWeight="700" letterSpacing="0.3">EMBEDDINGS</text>
          {/* Vector dot cluster */}
          {[
            { cx: 20, cy: 40, r: 4.5, fill: "#B9684E" },
            { cx: 38, cy: 34, r: 3.5, fill: "#87977B" },
            { cx: 28, cy: 52, r: 3.5, fill: "#40352F" },
            { cx: 50, cy: 46, r: 3.0, fill: "#87977B" },
            { cx: 64, cy: 38, r: 2.5, fill: "#B9684E" },
            { cx: 74, cy: 52, r: 2.5, fill: "#C4CEBC" },
            { cx: 88, cy: 42, r: 2.0, fill: "#D8C7B1" },
          ].map((d, i) => (
            <circle key={i} cx={d.cx} cy={d.cy} r={d.r} fill={d.fill} opacity="0.8" />
          ))}
          <line x1="20" y1="40" x2="38" y2="34" stroke="#C4CEBC" strokeWidth="0.9" />
          <line x1="38" y1="34" x2="50" y2="46" stroke="#C4CEBC" strokeWidth="0.9" />
          <line x1="28" y1="52" x2="50" y2="46" stroke="#C4CEBC" strokeWidth="0.9" />
          <line x1="50" y1="46" x2="64" y2="38" stroke="#C4CEBC" strokeWidth="0.8" />
          <line x1="64" y1="38" x2="74" y2="52" stroke="#C4CEBC" strokeWidth="0.8" />
          <line x1="74" y1="52" x2="88" y2="42" stroke="#C4CEBC" strokeWidth="0.7" />
        </g>

        {/* ════════════════════════════════════════════════════════
            BOTTOM LABELS
        ════════════════════════════════════════════════════════ */}
        <text
          x="142" y="398"
          fontSize="8.5"
          fill="#B9684E"
          fontWeight="700"
          letterSpacing="1"
          textAnchor="middle"
          fontFamily="Georgia, serif"
        >
          PDF · TXT
        </text>
        <text
          x="142" y="413"
          fontSize="7.5"
          fill="#87977B"
          fontWeight="600"
          letterSpacing="0.6"
          textAnchor="middle"
        >
          CHUNKS · EMBEDDINGS · QDRANT
        </text>
      </svg>
    </div>
  );
}
