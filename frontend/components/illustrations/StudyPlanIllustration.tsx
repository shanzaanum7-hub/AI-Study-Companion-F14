"use client";

/**
 * StudyPlanIllustration — v2
 * ───────────────────────────
 * Shown alongside the study-plan generator and after generation.
 *
 * Concept: a beautiful study planner card with:
 *   - Sage header band labelled "STUDY PLAN" + AI sparkle
 *   - Topic pill in terracotta
 *   - Four day rows: two with sage check marks (done), two with hollow
 *     circles (upcoming); active day highlighted in terracotta tint
 *   - Task sub-lines under each day
 *   - Clock + estimated-days row in the footer
 *   - Small floating terracotta sparkle outside the card (top-left)
 *   - Small floating sage dot cluster (top-right) for AI feel
 *
 * Only the card body floats — shadow stays static so the depth reads correctly.
 *
 * viewBox: 340 × 360  (wider/taller so all content has breathing room)
 */
export default function StudyPlanIllustration() {
  const days = [
    { label: "Day 1", focus: "Introduction",   tasks: ["Overview of concepts", "Read core material"],       done: true,  active: false },
    { label: "Day 2", focus: "Core Algorithms", tasks: ["Study scheduling types", "Compare approaches"],     done: true,  active: false },
    { label: "Day 3", focus: "Deep Dive",       tasks: ["Advanced scheduling", "Work through examples"],     done: false, active: true  },
    { label: "Day 4", focus: "Practice",        tasks: ["Solve past questions", "Review weak areas"],         done: false, active: false },
  ];

  // Card geometry
  const cardX = 44;
  const cardY = 42;
  const cardW = 252;
  const cardH = 272;
  const headerH = 38;
  const rowH = 54; // height allocated per day row
  const firstRowY = cardY + headerH + 28; // y of first day row content

  return (
    <div
      className="relative w-full max-w-[340px] mx-auto select-none"
      aria-hidden="true"
    >
      <svg
        viewBox="0 0 340 360"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        className="w-full h-auto"
      >
        {/* ── Soft background blob ─────────────────────────────── */}
        <ellipse cx="170" cy="175" rx="155" ry="158" fill="#EFF2EB" opacity="0.50" />

        {/* ── Dot grid (stays static) ──────────────────────────── */}
        {Array.from({ length: 6 }).map((_, r) =>
          Array.from({ length: 7 }).map((_, c) => (
            <circle
              key={`g-${r}-${c}`}
              cx={18 + c * 48}
              cy={18 + r * 56}
              r="1.3"
              fill="#D8C7B1"
              opacity="0.42"
            />
          ))
        )}

        {/* ── Static card shadow (does NOT float) ─────────────── */}
        <rect
          x={cardX + 4} y={cardY + 6}
          width={cardW} height={cardH}
          rx="12"
          fill="#40352F" opacity="0.07"
        />

        {/* ════════════════════════════════════════════════════════
            FLOATING CARD BODY
        ════════════════════════════════════════════════════════ */}
        <g
          className="animate-float"
          style={{ transformOrigin: `${cardX + cardW / 2}px ${cardY + cardH / 2}px` }}
        >
          {/* Card background */}
          <rect x={cardX} y={cardY} width={cardW} height={cardH} rx="12" fill="#FBF8F2" />

          {/* ── Header band ───────────────────────────────────── */}
          <rect x={cardX} y={cardY} width={cardW} height={headerH} rx="12" fill="#87977B" />
          {/* Fill the bottom corners of the header so they're square */}
          <rect x={cardX} y={cardY + headerH - 12} width={cardW} height="12" fill="#87977B" />

          {/* STUDY PLAN label */}
          <text
            x={cardX + 18} y={cardY + 24}
            fontSize="11"
            fill="#FBF8F2"
            fontWeight="700"
            letterSpacing="1.2"
            fontFamily="Georgia, serif"
          >
            STUDY PLAN
          </text>

          {/* AI sparkle in header (top-right) */}
          <g transform={`translate(${cardX + cardW - 24}, ${cardY + 19})`}>
            <line x1="0" y1="-6" x2="0" y2="6"   stroke="#FBF8F2" strokeWidth="1.5" strokeLinecap="round" />
            <line x1="-6" y1="0" x2="6" y2="0"   stroke="#FBF8F2" strokeWidth="1.5" strokeLinecap="round" />
            <line x1="-4" y1="-4" x2="4" y2="4"  stroke="#FBF8F2" strokeWidth="1"   strokeLinecap="round" opacity="0.55" />
            <line x1="4"  y1="-4" x2="-4" y2="4" stroke="#FBF8F2" strokeWidth="1"   strokeLinecap="round" opacity="0.55" />
          </g>

          {/* ── Topic row ─────────────────────────────────────── */}
          {/* Topic title line */}
          <rect
            x={cardX + 18} y={cardY + headerH + 12}
            width="120" height="7" rx="3.5"
            fill="#40352F" opacity="0.75"
          />
          {/* Topic pill */}
          <rect
            x={cardX + 146} y={cardY + headerH + 10}
            width="86" height="13" rx="6.5"
            fill="#B9684E" opacity="0.12"
          />
          <text
            x={cardX + 153} y={cardY + headerH + 20}
            fontSize="6.5"
            fill="#B9684E"
            fontWeight="700"
            letterSpacing="0.3"
          >
            CPU SCHEDULING
          </text>

          {/* Thin divider */}
          <rect
            x={cardX + 18} y={cardY + headerH + 28}
            width={cardW - 36} height="1"
            fill="#D8C7B1"
          />

          {/* ── Day rows ──────────────────────────────────────── */}
          {days.map((day, i) => {
            const rowY = firstRowY + 6 + i * rowH;

            return (
              <g key={day.label}>
                {/* Active row highlight */}
                {day.active && (
                  <rect
                    x={cardX + 10} y={rowY - 6}
                    width={cardW - 20} height={rowH - 4}
                    rx="7"
                    fill="#B9684E" opacity="0.055"
                  />
                )}

                {/* Done check / pending circle */}
                {day.done ? (
                  <g transform={`translate(${cardX + 18}, ${rowY + 1})`}>
                    <circle cx="9" cy="9" r="9" fill="#87977B" opacity="0.9" />
                    <path
                      d="M5 9 L8 12 L13.5 6"
                      stroke="#FBF8F2"
                      strokeWidth="1.6"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                    />
                  </g>
                ) : (
                  <circle
                    cx={cardX + 27}
                    cy={rowY + 10}
                    r="9"
                    fill="none"
                    stroke={day.active ? "#B9684E" : "#D8C7B1"}
                    strokeWidth={day.active ? 2 : 1.5}
                  />
                )}

                {/* Day label */}
                <text
                  x={cardX + 44}
                  y={rowY + 14}
                  fontSize="8.5"
                  fill={day.done ? "#87977B" : day.active ? "#40352F" : "#7A6A5E"}
                  fontWeight="700"
                >
                  {day.label}
                </text>

                {/* Focus text */}
                <text
                  x={cardX + 90}
                  y={rowY + 14}
                  fontSize="8"
                  fill={day.active ? "#40352F" : "#7A6A5E"}
                  fontWeight={day.active ? "600" : "400"}
                >
                  {day.focus}
                </text>

                {/* Task lines */}
                {day.tasks.map((_, ti) => (
                  <rect
                    key={ti}
                    x={cardX + 44}
                    y={rowY + 20 + ti * 10}
                    width={ti === 0 ? 148 : 120}
                    height="3.5"
                    rx="1.75"
                    fill={day.done ? "#87977B" : "#7A6A5E"}
                    opacity={day.done ? 0.22 : day.active ? 0.30 : 0.20}
                  />
                ))}

                {/* Row divider (except last) */}
                {i < days.length - 1 && (
                  <rect
                    x={cardX + 18}
                    y={rowY + rowH - 5}
                    width={cardW - 36}
                    height="0.8"
                    fill="#D8C7B1"
                    opacity="0.6"
                  />
                )}
              </g>
            );
          })}

          {/* ── Footer: estimated time ─────────────────────────── */}
          <rect
            x={cardX} y={cardY + cardH - 34}
            width={cardW} height="34"
            rx="12"
            fill="#EFF2EB"
          />
          {/* square-off the top corners of the footer */}
          <rect
            x={cardX} y={cardY + cardH - 34}
            width={cardW} height="12"
            fill="#EFF2EB"
          />

          {/* Clock icon */}
          <circle
            cx={cardX + 26} cy={cardY + cardH - 17}
            r="8"
            fill="none"
            stroke="#87977B"
            strokeWidth="1.5"
          />
          <line
            x1={cardX + 26} y1={cardY + cardH - 22}
            x2={cardX + 26} y2={cardY + cardH - 17}
            stroke="#87977B" strokeWidth="1.5" strokeLinecap="round"
          />
          <line
            x1={cardX + 26} y1={cardY + cardH - 17}
            x2={cardX + 30} y2={cardY + cardH - 14}
            stroke="#87977B" strokeWidth="1.5" strokeLinecap="round"
          />

          {/* Estimated days text */}
          <text
            x={cardX + 42} y={cardY + cardH - 13}
            fontSize="8"
            fill="#7A6A5E"
            fontWeight="500"
          >
            4 days estimated
          </text>

          {/* AI badge right side of footer */}
          <rect
            x={cardX + cardW - 50} y={cardY + cardH - 28}
            width="40" height="16"
            rx="8"
            fill="#87977B" opacity="0.15"
          />
          <text
            x={cardX + cardW - 42} y={cardY + cardH - 17}
            fontSize="7"
            fill="#87977B"
            fontWeight="700"
            letterSpacing="0.3"
          >
            AI · GEN
          </text>
        </g>
        {/* end floating group */}

        {/* ════════════════════════════════════════════════════════
            DECORATIVE ELEMENTS (static — outside floating group)
        ════════════════════════════════════════════════════════ */}

        {/* Terracotta sparkle — top-left */}
        <g transform="translate(24, 30)">
          <line x1="0" y1="-9" x2="0" y2="9"   stroke="#B9684E" strokeWidth="1.8" strokeLinecap="round" opacity="0.65" />
          <line x1="-9" y1="0" x2="9" y2="0"   stroke="#B9684E" strokeWidth="1.8" strokeLinecap="round" opacity="0.65" />
          <line x1="-6" y1="-6" x2="6" y2="6"  stroke="#B9684E" strokeWidth="1.1" strokeLinecap="round" opacity="0.35" />
          <line x1="6"  y1="-6" x2="-6" y2="6" stroke="#B9684E" strokeWidth="1.1" strokeLinecap="round" opacity="0.35" />
        </g>

        {/* Sage dot cluster — top-right (represents vectors/AI) */}
        {[
          { cx: 302, cy: 28, r: 5,   fill: "#87977B" },
          { cx: 316, cy: 20, r: 3.5, fill: "#B9684E" },
          { cx: 326, cy: 34, r: 3,   fill: "#87977B" },
          { cx: 312, cy: 40, r: 2.5, fill: "#C4CEBC" },
        ].map((d, i) => (
          <circle key={i} cx={d.cx} cy={d.cy} r={d.r} fill={d.fill} opacity="0.7" />
        ))}
        <line x1="302" y1="28" x2="316" y2="20" stroke="#C4CEBC" strokeWidth="0.9" opacity="0.7" />
        <line x1="316" y1="20" x2="326" y2="34" stroke="#C4CEBC" strokeWidth="0.9" opacity="0.7" />
        <line x1="312" y1="40" x2="326" y2="34" stroke="#C4CEBC" strokeWidth="0.9" opacity="0.6" />
        <line x1="302" y1="28" x2="312" y2="40" stroke="#C4CEBC" strokeWidth="0.8" opacity="0.5" />

        {/* Bottom label */}
        <text
          x="170" y="350"
          fontSize="8.5"
          fill="#87977B"
          fontWeight="600"
          letterSpacing="0.8"
          textAnchor="middle"
        >
          AI GENERATED STUDY PLAN
        </text>
      </svg>
    </div>
  );
}
