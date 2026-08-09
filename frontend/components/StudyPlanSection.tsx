"use client";

/**
 * StudyPlanSection
 * ─────────────────
 * Complete Step 3 section: generator panel + illustration on the right;
 * rendered study plan below after generation.
 *
 * Stages:
 *   idle       — generate button disabled until retrieval is done
 *   generating — spinner + "Creating your study plan…" message
 *   generated  — full StudyPlanDisplay rendered below
 *   error      — error banner with detail text
 *
 * Props:
 *   isEnabled   — false until retrieval has returned results
 *   query       — prefilled from the last retrieval query
 *   documentId  — scopes the plan retrieval (optional)
 */

import { useRef, useState, useEffect } from "react";
import { Sparkles, Loader2, AlertCircle, BookOpen, RefreshCw } from "lucide-react";
import clsx from "clsx";
import StudyPlanDisplay from "./StudyPlanDisplay";
import StudyPlanIllustration from "./illustrations/StudyPlanIllustration";
import { generateStudyPlan } from "@/lib/api/studyPlan";
import type { AppError, SimpleStudyPlanResponse } from "@/lib/api/types";

type Difficulty = "beginner" | "intermediate" | "advanced";

interface StudyPlanSectionProps {
  isEnabled: boolean;
  query?: string;
  documentId?: string;
}

export default function StudyPlanSection({
  isEnabled,
  query: initialQuery = "",
  documentId,
}: StudyPlanSectionProps) {
  const [query,      setQuery]      = useState(initialQuery);
  const [difficulty, setDifficulty] = useState<Difficulty>("intermediate");
  const [days,       setDays]       = useState(7);
  const [isGenerating, setIsGenerating] = useState(false);
  const [error,      setError]      = useState<AppError | null>(null);
  const [response,   setResponse]   = useState<SimpleStudyPlanResponse | null>(null);

  const planRef = useRef<HTMLDivElement>(null);

  const canGenerate = isEnabled && !isGenerating && query.trim().length >= 2;

  /* ── Sync query when parent provides a new retrieval query ─────── */
  useEffect(() => {
    if (initialQuery && initialQuery !== query) {
      setQuery(initialQuery);
    }
  // Only run when initialQuery changes from the parent
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [initialQuery]);

  async function handleGenerate() {
    if (!canGenerate) return;
    setError(null);
    setResponse(null);
    setIsGenerating(true);

    const { data, error: apiErr } = await generateStudyPlan({
      query: query.trim(),
      top_k: 5,
      duration_days: days,
      difficulty,
    });

    setIsGenerating(false);

    if (apiErr || !data) {
      setError(apiErr ?? { code: "GENERATE", message: "Generation failed." });
      return;
    }

    setResponse(data);
    setTimeout(() => {
      planRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
    }, 100);
  }

  const DIFFICULTIES: { value: Difficulty; label: string }[] = [
    { value: "beginner",     label: "Beginner"     },
    { value: "intermediate", label: "Intermediate" },
    { value: "advanced",     label: "Advanced"     },
  ];

  return (
    <section
      id="study-plan"
      className="section bg-background border-t border-border"
      aria-labelledby="study-plan-heading"
    >
      <div className="container-main">

        {/* ── Section heading ──────────────────────────────────── */}
        <div className="mb-10 md:mb-14 text-center">
          <p className="label-sm text-terracotta mb-2">
            AI STUDY COMPANION · STEP 3
          </p>
          <h2 className="heading-1 text-dark-brown" id="study-plan-heading">
            Generate Your Study Plan
          </h2>
          <p className="body-lg mx-auto mt-3 max-w-xl">
            Use the retrieved material to create a focused, day-by-day AI
            study plan grounded entirely in your uploaded content.
          </p>
        </div>

        {/* ── Two-column: generator + illustration ─────────────── */}
        <div className="grid grid-cols-1 gap-10 lg:grid-cols-2 lg:gap-14 items-start mb-12">

          {/* Left: generator form */}
          <div className="flex flex-col gap-5 animate-slide-up">
            <div className="card p-6 md:p-8 flex flex-col gap-6">

              {/* Card title */}
              <div>
                <p className="label-sm text-terracotta mb-1.5">Step 3 · AI Generation</p>
                <h3 className="heading-3 text-dark-brown">Generate Your Study Plan</h3>
                <p className="body-base mt-1.5">
                  The AI will retrieve relevant context from your document and
                  generate a structured day-by-day plan.
                </p>
              </div>

              {/* Query input */}
              <div className="flex flex-col gap-1.5">
                <label
                  htmlFor="sp-query"
                  className="text-xs font-semibold text-text-secondary uppercase tracking-wider"
                >
                  Topic or question
                </label>
                <input
                  id="sp-query"
                  type="text"
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  placeholder={isEnabled ? "e.g. CPU Scheduling" : "Complete Step 2 first"}
                  disabled={!isEnabled || isGenerating}
                  maxLength={300}
                  className={clsx(
                    "rounded-xl border px-4 py-3 text-sm outline-none transition-all bg-card",
                    "placeholder:text-text-secondary/50",
                    isEnabled && !isGenerating
                      ? "border-beige text-dark-brown hover:border-sage focus:border-terracotta focus:ring-2 focus:ring-terracotta/15"
                      : "border-beige/60 text-text-secondary cursor-not-allowed bg-background"
                  )}
                  aria-disabled={!isEnabled}
                />
              </div>

              {/* Difficulty selector */}
              <div className="flex flex-col gap-1.5">
                <p className="text-xs font-semibold text-text-secondary uppercase tracking-wider">
                  Difficulty
                </p>
                <div className="flex gap-2 flex-wrap" role="radiogroup" aria-label="Difficulty level">
                  {DIFFICULTIES.map((d) => (
                    <button
                      key={d.value}
                      type="button"
                      role="radio"
                      aria-checked={difficulty === d.value}
                      disabled={!isEnabled || isGenerating}
                      onClick={() => setDifficulty(d.value)}
                      className={clsx(
                        "rounded-xl border px-4 py-2 text-sm font-medium transition-all",
                        "focus-visible:outline focus-visible:outline-2 focus-visible:outline-terracotta",
                        "disabled:opacity-50 disabled:cursor-not-allowed",
                        difficulty === d.value
                          ? "border-terracotta bg-terracotta/8 text-terracotta font-semibold"
                          : "border-beige bg-card text-text-secondary hover:border-sage hover:bg-ai-bg"
                      )}
                    >
                      {d.label}
                    </button>
                  ))}
                </div>
              </div>

              {/* Duration slider */}
              <div className="flex flex-col gap-2">
                <div className="flex justify-between items-center">
                  <p className="text-xs font-semibold text-text-secondary uppercase tracking-wider">
                    Duration
                  </p>
                  <span className="text-sm font-bold text-dark-brown tabular-nums">
                    {days} day{days !== 1 ? "s" : ""}
                  </span>
                </div>
                <input
                  type="range"
                  min={1}
                  max={14}
                  value={days}
                  disabled={!isEnabled || isGenerating}
                  onChange={(e) => setDays(Number(e.target.value))}
                  className={clsx(
                    "w-full h-1.5 rounded-full appearance-none bg-beige outline-none",
                    "accent-terracotta cursor-pointer",
                    "disabled:opacity-50 disabled:cursor-not-allowed"
                  )}
                  aria-label={`Study plan duration: ${days} days`}
                />
                <div className="flex justify-between text-[10px] text-text-secondary/60">
                  <span>1 day</span>
                  <span>14 days</span>
                </div>
              </div>

              {/* Error */}
              {error && (
                <div
                  role="alert"
                  className="flex items-start gap-3 rounded-xl border border-terracotta/25
                             bg-terracotta/6 px-4 py-3"
                >
                  <AlertCircle className="h-4 w-4 text-terracotta shrink-0 mt-0.5" aria-hidden="true" />
                  <div>
                    <p className="text-sm font-semibold text-terracotta">{error.message}</p>
                    {error.details && (
                      <p className="text-xs text-text-secondary mt-0.5">{error.details}</p>
                    )}
                  </div>
                </div>
              )}

              {/* Generate button */}
              <button
                type="button"
                onClick={handleGenerate}
                disabled={!canGenerate}
                className="btn-primary w-full justify-center py-3.5 text-base"
                aria-busy={isGenerating}
                aria-disabled={!canGenerate}
              >
                {isGenerating ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />
                    Creating your study plan…
                  </>
                ) : response ? (
                  <>
                    <RefreshCw className="h-4 w-4" aria-hidden="true" />
                    Regenerate Study Plan
                  </>
                ) : (
                  <>
                    <Sparkles className="h-4 w-4" aria-hidden="true" />
                    Generate Study Plan
                  </>
                )}
              </button>

              {/* Locked note */}
              {!isEnabled && (
                <div className="flex items-center gap-2.5 rounded-xl border border-beige bg-background px-4 py-3">
                  <BookOpen className="h-4 w-4 text-beige shrink-0" aria-hidden="true" />
                  <p className="text-xs text-text-secondary">
                    Retrieve relevant content in Step 2 to unlock plan generation.
                  </p>
                </div>
              )}
            </div>

            {/* Generating animation card */}
            {isGenerating && (
              <div
                className="card px-6 py-8 flex flex-col items-center gap-4 text-center
                           animate-fade-in bg-ai-bg border-sage/20"
                role="status"
                aria-live="polite"
                aria-label="Generating study plan"
              >
                <span className="flex h-12 w-12 items-center justify-center rounded-full bg-sage/20">
                  <Sparkles className="h-6 w-6 text-sage animate-pulse-slow" aria-hidden="true" />
                </span>
                <div>
                  <p className="text-sm font-semibold text-dark-brown">
                    Creating your study plan from the retrieved material…
                  </p>
                  <p className="text-xs text-text-secondary mt-1">
                    Gemini is reading your context chunks and structuring a personalised plan.
                  </p>
                </div>
                {/* Animated dots */}
                <div className="flex gap-1.5" aria-hidden="true">
                  {[0, 1, 2, 3].map((i) => (
                    <span
                      key={i}
                      className="h-1.5 w-1.5 rounded-full bg-sage animate-bounce"
                      style={{ animationDelay: `${i * 150}ms` }}
                    />
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Right: illustration */}
          <div className="flex flex-col items-center justify-start gap-4 animate-fade-in animation-delay-200">
            <StudyPlanIllustration />
            <p className="text-center text-xs text-text-secondary leading-relaxed max-w-xs">
              Retrieved context chunks are assembled into a Gemini prompt.
              The response is validated as structured JSON and rendered as
              your personalised study schedule.
            </p>
            {/* Legend */}
            <div className="flex flex-wrap gap-3 justify-center">
              {[
                { dot: "#B9684E", label: "Retrieved context" },
                { dot: "#87977B", label: "Gemini LLM"        },
                { dot: "#40352F", label: "Structured plan"   },
              ].map((item, i) => (
                <span key={item.label} className="flex items-center gap-1.5 text-xs text-text-secondary">
                  {i > 0 && <span className="text-beige" aria-hidden="true">→</span>}
                  <span className="h-2 w-2 rounded-full shrink-0" style={{ backgroundColor: item.dot }} aria-hidden="true" />
                  {item.label}
                </span>
              ))}
            </div>
          </div>
        </div>

        {/* ── Generated plan (full-width below columns) ─────────── */}
        {response && (
          <div
            ref={planRef}
            className="animate-slide-up border-t border-border pt-10"
          >
            {/* Success banner */}
            <div
              role="status"
              aria-live="polite"
              className="mb-6 flex items-center gap-3 rounded-xl border border-sage/25
                         bg-ai-bg px-5 py-4"
            >
              <span
                className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-sage/20"
                aria-hidden="true"
              >
                <Sparkles className="h-5 w-5 text-sage" />
              </span>
              <div>
                <p className="text-sm font-semibold text-dark-brown">
                  Study plan generated successfully
                </p>
                <p className="text-xs text-text-secondary">
                  {response.plan?.estimated_days ?? 0} days ·{" "}
                  {(response.plan?.study_plan ?? []).length} sessions ·{" "}
                  {response.chunks_used} context chunk{response.chunks_used !== 1 ? "s" : ""} used
                </p>
              </div>
            </div>

            <StudyPlanDisplay response={response} />
          </div>
        )}

      </div>
    </section>
  );
}
