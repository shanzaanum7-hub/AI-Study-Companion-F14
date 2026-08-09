"use client";

/**
 * ProcessingStatus
 * ─────────────────
 * Visualises the 5-step backend pipeline:
 *   Document uploaded → Extracting text → Creating chunks →
 *   Generating embeddings → Storing in Qdrant
 *
 * Every step has four states:
 *   pending    ○  hollow circle, muted text
 *   processing ◎  terracotta ring + spinning loader, bold label + detail
 *   completed  ✓  filled sage circle + check, green label
 *   failed     ✕  filled terracotta circle + X, error text
 *
 * Accessibility: step list is an <ol> with role="list", each item has an
 * sr-only status prefix so screen readers announce "Completed: Extracting text".
 */

import { CheckCircle2, Loader2, XCircle } from "lucide-react";
import clsx from "clsx";
import type { ProcessingStep } from "@/lib/api/types";

/* ── Step metadata (icon, colour, description) ───────────────────────── */
const STEP_META: Record<string, { detail: string }> = {
  upload:  { detail: "File received and saved to the server"       },
  extract: { detail: "Reading and cleaning raw text from the file" },
  chunk:   { detail: "Splitting content into semantic segments"    },
  embed:   { detail: "Converting chunks to 768-dim Gemini vectors" },
  store:   { detail: "Persisting vectors in Qdrant study_notes"    },
};

interface ProcessingStatusProps {
  steps: ProcessingStep[];
}

export default function ProcessingStatus({ steps }: ProcessingStatusProps) {
  const allDone   = steps.length > 0 && steps.every((s) => s.status === "completed");
  const hasFailed = steps.some((s) => s.status === "failed");
  const activeIdx = steps.findIndex((s) => s.status === "processing");

  return (
    <div className="card overflow-hidden">

      {/* ── Card header ──────────────────────────────────────────── */}
      <div className="flex items-center justify-between border-b border-border bg-background px-5 py-4">
        <div>
          <p className="label-sm text-terracotta mb-0.5">Pipeline</p>
          <h3 className="heading-3 text-dark-brown">Processing Your Document</h3>
        </div>

        {/* Status badge */}
        {allDone && !hasFailed && (
          <span className="badge-sage shrink-0">
            <CheckCircle2 className="h-3.5 w-3.5" aria-hidden="true" />
            Complete
          </span>
        )}
        {hasFailed && (
          <span className="badge-terracotta shrink-0">
            <XCircle className="h-3.5 w-3.5" aria-hidden="true" />
            Failed
          </span>
        )}
        {!allDone && !hasFailed && activeIdx >= 0 && (
          <span className="inline-flex items-center gap-1.5 rounded-full bg-terracotta/10 px-3 py-1
                           text-xs font-semibold text-terracotta shrink-0">
            <Loader2 className="h-3 w-3 animate-spin" aria-hidden="true" />
            Step {activeIdx + 1} of {steps.length}
          </span>
        )}
      </div>

      {/* ── Step list ────────────────────────────────────────────── */}
      <ol
        className="flex flex-col divide-y divide-border/50"
        aria-label="Document processing pipeline steps"
      >
        {steps.map((step, index) => {
          const isActive  = step.status === "processing";
          const isDone    = step.status === "completed";
          const isFailed  = step.status === "failed";
          const isPending = step.status === "pending";
          const meta      = STEP_META[step.id] ?? { detail: "" };

          return (
            <li
              key={step.id}
              className={clsx(
                "flex items-start gap-4 px-5 py-4 transition-colors duration-300",
                isActive  && "bg-terracotta/[0.04]",
                isDone    && "bg-transparent",
                isPending && "opacity-60"
              )}
            >
              {/* ── Step number + icon ─────────────────────────── */}
              <div className="flex flex-col items-center shrink-0 pt-0.5">
                {/* Circle icon */}
                <span
                  className={clsx(
                    "flex h-9 w-9 items-center justify-center rounded-full border-2",
                    "transition-all duration-300",
                    isDone    && "border-sage bg-sage shadow-sm",
                    isActive  && "border-terracotta bg-terracotta/10 shadow-[0_0_0_4px_rgba(185,104,78,0.12)]",
                    isFailed  && "border-terracotta bg-terracotta",
                    isPending && "border-beige bg-background"
                  )}
                  aria-hidden="true"
                >
                  {isDone && (
                    <CheckCircle2 className="h-4.5 w-4.5 text-white" />
                  )}
                  {isActive && (
                    <Loader2 className="h-4 w-4 animate-spin text-terracotta" />
                  )}
                  {isFailed && (
                    <XCircle className="h-4.5 w-4.5 text-white" />
                  )}
                  {isPending && (
                    <span className="text-xs font-bold text-beige">{index + 1}</span>
                  )}
                </span>

                {/* Vertical connector to next step */}
                {index < steps.length - 1 && (
                  <span
                    className={clsx(
                      "mt-1 w-0.5 flex-1 rounded-full transition-all duration-700",
                      "min-h-[20px]",
                      isDone ? "bg-sage/40" : "bg-beige/60"
                    )}
                    aria-hidden="true"
                  />
                )}
              </div>

              {/* ── Step content ───────────────────────────────── */}
              <div className="flex-1 min-w-0 pb-1">
                {/* Step number label (pending) or status text (others) */}
                <div className="flex items-center gap-2 mb-0.5">
                  {!isPending && (
                    <span className="label-sm">
                      {isDone   ? "Completed"   : ""}
                      {isActive ? "In progress" : ""}
                      {isFailed ? "Failed"      : ""}
                    </span>
                  )}
                  {isPending && (
                    <span className="label-sm">Step {index + 1}</span>
                  )}
                </div>

                {/* Main label */}
                <p
                  className={clsx(
                    "text-sm font-semibold leading-snug transition-colors",
                    isDone    && "text-sage",
                    isActive  && "text-dark-brown",
                    isFailed  && "text-terracotta",
                    isPending && "text-text-secondary"
                  )}
                >
                  {/* Screen-reader status prefix */}
                  <span className="sr-only">
                    {isDone   && "Completed: "}
                    {isActive && "In progress: "}
                    {isFailed && "Failed: "}
                    {isPending && "Pending: "}
                  </span>
                  {step.label}
                </p>

                {/* Detail text */}
                {(isActive || isDone) && meta.detail && (
                  <p
                    className={clsx(
                      "text-xs mt-0.5 leading-relaxed",
                      isDone   ? "text-sage/80" : "text-text-secondary"
                    )}
                  >
                    {meta.detail}
                  </p>
                )}

                {/* Animated "working" sub-label for active step */}
                {isActive && (
                  <p
                    className="text-xs text-terracotta font-medium mt-1.5
                               flex items-center gap-1.5"
                    aria-live="polite"
                    aria-label="Step in progress"
                  >
                    <span
                      className="inline-block h-1.5 w-1.5 rounded-full bg-terracotta
                                 animate-bounce [animation-delay:0ms]"
                      aria-hidden="true"
                    />
                    <span
                      className="inline-block h-1.5 w-1.5 rounded-full bg-terracotta
                                 animate-bounce [animation-delay:150ms]"
                      aria-hidden="true"
                    />
                    <span
                      className="inline-block h-1.5 w-1.5 rounded-full bg-terracotta
                                 animate-bounce [animation-delay:300ms]"
                      aria-hidden="true"
                    />
                    <span className="ml-0.5">Working…</span>
                  </p>
                )}
              </div>

              {/* ── Right: check or number badge ───────────────── */}
              <div className="shrink-0 pt-0.5">
                {isDone && (
                  <span
                    className="flex h-6 w-6 items-center justify-center rounded-full
                               bg-sage/15 text-sage"
                    aria-hidden="true"
                  >
                    <CheckCircle2 className="h-3.5 w-3.5" />
                  </span>
                )}
                {(isActive || isPending) && (
                  <span
                    className={clsx(
                      "flex h-6 min-w-[1.5rem] items-center justify-center rounded-full",
                      "text-xs font-bold px-1.5",
                      isActive
                        ? "bg-terracotta/10 text-terracotta"
                        : "bg-beige/50 text-text-secondary"
                    )}
                    aria-hidden="true"
                  >
                    {String(index + 1).padStart(2, "0")}
                  </span>
                )}
              </div>
            </li>
          );
        })}
      </ol>

      {/* ── Footer banners ───────────────────────────────────────── */}
      {allDone && !hasFailed && (
        <div
          role="status"
          aria-live="polite"
          className="flex items-center gap-3 border-t border-sage/20 bg-ai-bg px-5 py-4"
        >
          <span
            className="flex h-9 w-9 shrink-0 items-center justify-center
                       rounded-full bg-sage/20"
            aria-hidden="true"
          >
            <CheckCircle2 className="h-5 w-5 text-sage" />
          </span>
          <div>
            <p className="text-sm font-semibold text-dark-brown">
              Document successfully indexed
            </p>
            <p className="text-xs text-text-secondary">
              Ready for semantic retrieval and study-plan generation
            </p>
          </div>
        </div>
      )}

      {hasFailed && (
        <div
          role="alert"
          className="flex items-center gap-3 border-t border-terracotta/20
                     bg-terracotta/5 px-5 py-4"
        >
          <span
            className="flex h-9 w-9 shrink-0 items-center justify-center
                       rounded-full bg-terracotta/15"
            aria-hidden="true"
          >
            <XCircle className="h-5 w-5 text-terracotta" />
          </span>
          <div>
            <p className="text-sm font-semibold text-terracotta">
              Processing failed
            </p>
            <p className="text-xs text-text-secondary">
              Please try uploading a different file or check the backend logs.
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
