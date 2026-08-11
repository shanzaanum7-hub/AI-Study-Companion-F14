"use client";

/**
 * app/page.tsx — AI Study Companion main page
 * ─────────────────────────────────────────────
 * Owns the top-level app state and wires all three workflow sections:
 *
 *   Step 1 — Upload   (UploadSection)
 *   Step 2 — Retrieve (RetrievalSection)
 *   Step 3 — Plan     (StudyPlanSection)
 *
 * State flow:
 *   ┌──────────┐  onDocumentReady  ┌──────────────┐  onResultsReady  ┌─────────────────┐
 *   │  Upload  │ ────────────────► │  Retrieval   │ ───────────────► │   Study Plan    │
 *   └──────────┘                   └──────────────┘                   └─────────────────┘
 *
 * - documentId is passed down so retrieval can scope its search.
 * - lastQuery is passed to StudyPlanSection so the topic field is pre-filled.
 * - Both Retrieval and Study Plan unlock only after the previous step completes.
 *
 * No server-side data fetching — all API calls happen inside the child sections.
 */

import { useRef, useState, useEffect } from "react";
import Navbar from "@/components/Navbar";
import Footer from "@/components/Footer";
import UploadSection from "@/components/UploadSection";
import RetrievalSection from "@/components/RetrievalSection";
import StudyPlanSection from "@/components/StudyPlanSection";
import type { UploadResponse } from "@/lib/api/types";

export default function HomePage() {
  /* ── App-level state ──────────────────────────────────────────── */
  const [documentReady, setDocumentReady] = useState(false);
  const [documentId,    setDocumentId]    = useState<string | undefined>();
  const [retrievalDone, setRetrievalDone] = useState(false);
  const [lastQuery,     setLastQuery]     = useState("");
  const [activeSection, setActiveSection] = useState<"workspace" | "how-it-works">("workspace");

  /* ── Section refs for smooth scroll ──────────────────────────── */
  const retrievalRef  = useRef<HTMLDivElement>(null);
  const studyPlanRef  = useRef<HTMLDivElement>(null);

  /* ── Handlers ────────────────────────────────────────────────── */
  function handleDocumentReady(doc: UploadResponse) {
    setDocumentId(doc.document_id);
    setDocumentReady(true);
    // Scroll to retrieval section after a brief delay so the upload
    // success UI is visible before the page moves
    setTimeout(() => {
      retrievalRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
    }, 600);
  }

  function handleResultsReady(query: string) {
    setLastQuery(query);
    setRetrievalDone(true);
    setTimeout(() => {
      studyPlanRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
    }, 400);
  }

  /* ── Navbar navigation (smooth scroll to section IDs) ─────────── */
  function handleNavigate(section: "workspace" | "how-it-works") {
    setActiveSection(section);
    if (section === "workspace") {
      window.scrollTo({ top: 0, behavior: "smooth" });
    } else {
      document.getElementById("how-it-works")?.scrollIntoView({ behavior: "smooth" });
    }
  }

  return (
    <>
      {/* ── Navigation ───────────────────────────────────────────── */}
      <Navbar activeSection={activeSection} onNavigate={handleNavigate} />

      {/* ── Main content ──────────────────────────────────────────── */}
      <main id="main-content">

        {/* ── HERO ──────────────────────────────────────────────── */}
        <section
          className="section bg-background dot-bg"
          aria-labelledby="hero-heading"
        >
          <div className="container-main">
            <div className="grid grid-cols-1 gap-10 lg:grid-cols-2 lg:gap-16 items-center">

              {/* Left: copy */}
              <div className="flex flex-col gap-6 animate-slide-up">
                {/* Eyebrow */}
                <p className="label-sm text-terracotta">
                  AI STUDY COMPANION · WEEK 3
                </p>

                {/* Heading */}
                <h1
                  id="hero-heading"
                  className="heading-display text-balance"
                >
                  Study Smarter<br />
                  <span className="text-terracotta">with Your Notes</span>
                </h1>

                {/* Sub */}
                <p className="body-lg max-w-md text-balance">
                  Upload your syllabus or study notes, retrieve the most
                  relevant content with semantic AI search, and generate a
                  focused day-by-day study plan.
                </p>

                {/* CTAs */}
                <div className="flex flex-wrap gap-3 pt-2">
                  <a
                    href="#upload"
                    className="btn-primary"
                    aria-label="Upload your study notes"
                  >
                    Upload Notes
                  </a>
                  <a
                    href="#how-it-works"
                    className="btn-secondary"
                    aria-label="See how the workflow works"
                  >
                    How It Works
                  </a>
                </div>

                {/* Step pill row */}
                <div className="flex flex-wrap gap-2 pt-2">
                  {[
                    { step: "01", label: "Upload"    },
                    { step: "02", label: "Retrieve"  },
                    { step: "03", label: "Study Plan" },
                  ].map((item, i) => (
                    <span
                      key={item.step}
                      className="flex items-center gap-1.5 text-xs text-text-secondary"
                    >
                      {i > 0 && <span className="text-beige" aria-hidden="true">→</span>}
                      <span
                        className="flex h-5 w-5 items-center justify-center rounded-full
                                   bg-terracotta text-white text-[9px] font-bold"
                        aria-hidden="true"
                      >
                        {item.step}
                      </span>
                      {item.label}
                    </span>
                  ))}
                </div>
              </div>

              {/* Right: hero illustration */}
              <div className="animate-fade-in animation-delay-300">
                <HeroVisual />
              </div>
            </div>
          </div>
        </section>

        {/* ── HOW IT WORKS ──────────────────────────────────────── */}
        <section
          id="how-it-works"
          className="section bg-off-white border-t border-border"
          aria-labelledby="how-it-works-heading"
        >
          <div className="container-main">
            <div className="text-center mb-12">
              <p className="label-sm text-terracotta mb-2">WORKFLOW</p>
              <h2 className="heading-1 text-dark-brown" id="how-it-works-heading">
                How It Works
              </h2>
              <p className="body-lg mt-3 max-w-xl mx-auto">
                Six steps from raw document to intelligent study plan.
              </p>
            </div>

            <WorkflowSteps />
          </div>
        </section>

        {/* ── STEP 1: UPLOAD ────────────────────────────────────── */}
        <div id="upload">
          <UploadSection onDocumentReady={handleDocumentReady} />
        </div>

        {/* ── STEP 2: RETRIEVE ──────────────────────────────────── */}
        <div ref={retrievalRef}>
          <RetrievalSection
            isEnabled={documentReady}
            documentId={documentId}
            onResultsReady={handleResultsReady}
          />
        </div>

        {/* ── STEP 3: STUDY PLAN ────────────────────────────────── */}
        <div ref={studyPlanRef}>
          <StudyPlanSection
            isEnabled={retrievalDone}
            query={lastQuery}
            documentId={documentId}
          />
        </div>

      </main>

      {/* ── Footer ───────────────────────────────────────────────── */}
      <Footer />
    </>
  );
}

/* ════════════════════════════════════════════════════════════════════
   HERO VISUAL — inline SVG so no external asset needed
════════════════════════════════════════════════════════════════════ */

function HeroVisual() {
  return (
    <div
      className="w-full max-w-[480px] mx-auto select-none"
      aria-hidden="true"
    >
      <svg
        viewBox="0 0 480 400"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        className="w-full h-auto"
      >
        {/* Background blob */}
        <ellipse cx="240" cy="200" rx="220" ry="185" fill="#EFF2EB" opacity="0.55" />

        {/* Dot grid */}
        {Array.from({ length: 7 }).map((_, r) =>
          Array.from({ length: 9 }).map((_, c) => (
            <circle key={`d-${r}-${c}`} cx={20 + c * 54} cy={20 + r * 54} r="1.4" fill="#D8C7B1" opacity="0.45" />
          ))
        )}

        {/* ── Floating main document ── */}
        <g className="animate-float" style={{ transformOrigin: "200px 190px" }}>
          {/* shadow */}
          <rect x="114" y="56" width="148" height="190" rx="10" fill="#40352F" opacity="0.07" transform="translate(3,4)" />
          {/* body */}
          <rect x="114" y="56" width="148" height="190" rx="10" fill="#FBF8F2" />
          {/* header */}
          <rect x="114" y="56" width="148" height="28" rx="10" fill="#B9684E" />
          <rect x="114" y="70"  width="148" height="14" fill="#B9684E" />
          <text x="130" y="74" fontSize="9" fill="#FBF8F2" fontWeight="700" letterSpacing="0.8">STUDY NOTES</text>
          {/* text lines */}
          <rect x="130" y="96"  width="116" height="6"   rx="3"    fill="#40352F" opacity="0.7" />
          {[104,112,120,130,140,148,158,168,176,186,194,204,212,220,230].map((y,i)=>(
            <rect key={y} x="130" y={y} width={i%3===0?116:i%3===1?94:104} height="3.5" rx="1.75" fill={i%4===0?"#87977B":"#7A6A5E"} opacity={i%4===0?0.4:0.28} />
          ))}
          {/* corner fold */}
          <path d="M244 56 L262 56 L244 74 Z" fill="#D8C7B1" opacity="0.9" />
          {/* sparkle */}
          <g transform="translate(270,48)">
            <line x1="0" y1="-7" x2="0" y2="7"  stroke="#B9684E" strokeWidth="1.5" strokeLinecap="round" />
            <line x1="-7" y1="0" x2="7" y2="0"  stroke="#B9684E" strokeWidth="1.5" strokeLinecap="round" />
            <line x1="-4" y1="-4" x2="4" y2="4" stroke="#B9684E" strokeWidth="1"   strokeLinecap="round" opacity="0.55" />
            <line x1="4"  y1="-4" x2="-4" y2="4" stroke="#B9684E" strokeWidth="1"  strokeLinecap="round" opacity="0.55" />
          </g>
        </g>

        {/* ── Search lens ── */}
        <g transform="translate(332,120)" className="animate-float" style={{ animationDelay: "1s", transformOrigin: "32px 32px" }}>
          <circle cx="32" cy="32" r="32" fill="#EFF2EB" opacity="0.7" />
          <circle cx="32" cy="32" r="22" fill="none" stroke="#87977B" strokeWidth="2.5" />
          <line  x1="48" y1="48" x2="60" y2="60" stroke="#87977B" strokeWidth="3.5" strokeLinecap="round" />
          <circle cx="26" cy="26" r="3"  fill="#B9684E" opacity="0.45" />
        </g>

        {/* Connector arrow */}
        <path d="M262 180 Q300 178 332 152" stroke="#D8C7B1" strokeWidth="1.5" strokeDasharray="5 3" fill="none" markerEnd="url(#hArr)" />

        {/* ── Study plan mini card ── */}
        <g transform="translate(340,255)">
          <rect width="120" height="108" rx="9" fill="#FBF8F2" stroke="#D8C7B1" strokeWidth="1" />
          <rect width="120" height="24"  rx="9" fill="#87977B" opacity="0.9" />
          <rect y="15" width="120" height="9" fill="#87977B" opacity="0.9" />
          <text x="14" y="16" fontSize="8" fill="#FBF8F2" fontWeight="700" letterSpacing="0.8">STUDY PLAN</text>
          {[
            { y:36, done:true  },
            { y:55, done:true  },
            { y:74, done:false },
            { y:93, done:false },
          ].map((row,i)=>(
            <g key={i}>
              {row.done
                ? <><circle cx="18" cy={row.y+4} r="6" fill="#87977B" opacity="0.85"/>
                    <path d={`M15 ${row.y+4} L17.5 ${row.y+6.5} L22 ${row.y+1.5}`} stroke="#FBF8F2" strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round"/></>
                : <circle cx="18" cy={row.y+4} r="6" fill="none" stroke="#D8C7B1" strokeWidth="1.4"/>
              }
              <rect x="30" y={row.y} width={row.done?70:60} height="4"   rx="2" fill={row.done?"#87977B":"#7A6A5E"} opacity={row.done?0.3:0.22} />
              <rect x="30" y={row.y+8} width={row.done?56:50} height="3" rx="1.5" fill="#7A6A5E" opacity="0.18" />
            </g>
          ))}
        </g>

        {/* Arrow to plan card */}
        <path d="M364 228 Q364 240 390 255" stroke="#87977B" strokeWidth="1.5" strokeDasharray="5 3" fill="none" markerEnd="url(#hArrSage)" />

        {/* Embedding dots */}
        {[{cx:76,cy:130},{cx:94,cy:116},{cx:84,cy:150},{cx:104,cy:140},{cx:72,cy:158}].map((d,i)=>(
          <circle key={i} cx={d.cx} cy={d.cy} r={4-i*0.4} fill="#87977B" opacity="0.65"
            style={{animation:"pulseDot 2.4s ease-in-out infinite", animationDelay:`${i*0.3}s`}} />
        ))}
        <line x1="76"  y1="130" x2="94"  y2="116" stroke="#C4CEBC" strokeWidth="0.9" opacity="0.6" />
        <line x1="94"  y1="116" x2="84"  y2="150" stroke="#C4CEBC" strokeWidth="0.9" opacity="0.6" />
        <line x1="84"  y1="150" x2="104" y2="140" stroke="#C4CEBC" strokeWidth="0.9" opacity="0.5" />
        <line x1="76"  y1="130" x2="72"  y2="158" stroke="#C4CEBC" strokeWidth="0.8" opacity="0.5" />

        {/* Label dots */}
        <text x="88" y="195" fontSize="7.5" fill="#87977B" fontWeight="600" letterSpacing="0.5" textAnchor="middle">VECTORS</text>

        <defs>
          <marker id="hArr"     markerWidth="7" markerHeight="7" refX="6" refY="3.5" orient="auto"><path d="M0,.5 L6,3.5 L0,6.5 Z" fill="#D8C7B1"/></marker>
          <marker id="hArrSage" markerWidth="7" markerHeight="7" refX="6" refY="3.5" orient="auto"><path d="M0,.5 L6,3.5 L0,6.5 Z" fill="#87977B"/></marker>
        </defs>
      </svg>
    </div>
  );
}

/* ════════════════════════════════════════════════════════════════════
   WORKFLOW STEPS — horizontal on desktop, vertical on mobile
════════════════════════════════════════════════════════════════════ */

const STEPS = [
  { num: "01", title: "Document",   desc: "Upload your syllabus or notes.",                           color: "bg-terracotta" },
  { num: "02", title: "Chunks",     desc: "Split content into meaningful segments.",                  color: "bg-terracotta/80" },
  { num: "03", title: "Embeddings", desc: "Convert text chunks into searchable vectors.",             color: "bg-sage" },
  { num: "04", title: "Qdrant",     desc: "Store knowledge for fast retrieval.",                      color: "bg-sage/80" },
  { num: "05", title: "Retrieval",  desc: "Find the most relevant content.",                          color: "bg-sage" },
  { num: "06", title: "Study Plan", desc: "Turn retrieved knowledge into a focused plan.",            color: "bg-dark-brown" },
];

function WorkflowSteps() {
  return (
    <div className="relative">
      {/* Connecting line — desktop only */}
      <div
        className="absolute top-10 left-0 right-0 h-px bg-beige hidden lg:block"
        aria-hidden="true"
      />

      <ol className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-6 lg:gap-4">
        {STEPS.map((step) => (
          <li
            key={step.num}
            className="relative flex flex-col items-center text-center gap-3 lg:gap-4"
          >
            {/* Number bubble */}
            <span
              className={`relative z-10 flex h-10 w-10 shrink-0 items-center justify-center
                         rounded-full text-sm font-bold text-white ${step.color}`}
              aria-hidden="true"
            >
              {step.num}
            </span>

            {/* Content */}
            <div className="flex flex-col gap-1.5">
              <p className="text-sm font-bold text-dark-brown">{step.title}</p>
              <p className="text-xs text-text-secondary leading-relaxed">{step.desc}</p>
            </div>
          </li>
        ))}
      </ol>
    </div>
  );
}
