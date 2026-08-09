"use client";

/**
 * StudyPlanDisplay
 * ─────────────────
 * Renders the structured JSON returned by POST /api/study-plan into a
 * beautiful, readable study interface.
 *
 * Safety contract:
 *   - Never crashes on missing or malformed fields from the backend.
 *   - Every field access is guarded (optional chaining + fallbacks).
 *   - The component is purely presentational — no API calls.
 *
 * Layout:
 *   Header card  — topic, model, chunks used, tokens, estimated days
 *   Day cards    — one per StudyPlanDay, showing focus + task list
 *
 * Day card visual states:
 *   Completed  (day ≤ today mock)  — sage header, check marks
 *   Current    (first incomplete)  — terracotta accent
 *   Upcoming   — neutral cream card
 */

import { CheckCircle2, Clock, BookOpen, Sparkles, Hash, Brain } from "lucide-react";
import clsx from "clsx";
import type { SimpleStudyPlanResponse, StudyPlanDay } from "@/lib/api/types";

interface StudyPlanDisplayProps {
  response: SimpleStudyPlanResponse;
}

export default function StudyPlanDisplay({ response }: StudyPlanDisplayProps) {
  /* ── Safe field extraction ──────────────────────────────────── */
  const query        = response?.query        ?? "";
  const modelUsed    = response?.model_used   ?? "AI";
  const chunksUsed   = response?.chunks_used  ?? 0;
  const tokensUsed   = response?.tokens_used  ?? null;
  const plan         = response?.plan;
  const topic        = plan?.topic            ?? query ?? "Study Plan";
  const estimatedDays = plan?.estimated_days  ?? 0;
  const studyPlan    = Array.isArray(plan?.study_plan) ? plan.study_plan : [];

  /* ── Which day is "current" (first with tasks) ──────────────── */
  const currentDayIndex = 0; // in a real app: compare to today

  return (
    <div className="flex flex-col gap-6">

      {/* ── Plan header card ────────────────────────────────────── */}
      <div className="card overflow-hidden">

        {/* AI-generated banner */}
        <div className="flex items-center gap-2 border-b border-border bg-ai-bg px-5 py-3">
          <Sparkles className="h-4 w-4 text-sage shrink-0" aria-hidden="true" />
          <span className="text-xs font-semibold text-sage">AI-Generated Study Plan</span>
          <span className="ml-auto text-xs text-text-secondary font-mono">{modelUsed}</span>
        </div>

        {/* Topic + metadata */}
        <div className="px-5 py-5">
          <p className="label-sm text-terracotta mb-1.5">Topic</p>
          <h3 className="heading-2 text-dark-brown leading-snug mb-4">{topic}</h3>

          {/* Stats row */}
          <div className="flex flex-wrap gap-3">
            {/* Estimated days */}
            <div className="flex items-center gap-2 rounded-xl border border-border bg-background px-3.5 py-2.5">
              <Clock className="h-4 w-4 text-sage shrink-0" aria-hidden="true" />
              <div>
                <p className="text-xs text-text-secondary leading-none">Duration</p>
                <p className="text-sm font-bold text-dark-brown mt-0.5">
                  {estimatedDays} day{estimatedDays !== 1 ? "s" : ""}
                </p>
              </div>
            </div>

            {/* Days in plan */}
            <div className="flex items-center gap-2 rounded-xl border border-border bg-background px-3.5 py-2.5">
              <BookOpen className="h-4 w-4 text-sage shrink-0" aria-hidden="true" />
              <div>
                <p className="text-xs text-text-secondary leading-none">Sessions</p>
                <p className="text-sm font-bold text-dark-brown mt-0.5">
                  {studyPlan.length} day{studyPlan.length !== 1 ? "s" : ""}
                </p>
              </div>
            </div>

            {/* Context chunks */}
            <div className="flex items-center gap-2 rounded-xl border border-border bg-background px-3.5 py-2.5">
              <Hash className="h-4 w-4 text-sage shrink-0" aria-hidden="true" />
              <div>
                <p className="text-xs text-text-secondary leading-none">Context</p>
                <p className="text-sm font-bold text-dark-brown mt-0.5">
                  {chunksUsed} chunk{chunksUsed !== 1 ? "s" : ""}
                </p>
              </div>
            </div>

            {/* Tokens */}
            {tokensUsed != null && (
              <div className="flex items-center gap-2 rounded-xl border border-border bg-background px-3.5 py-2.5">
                <Brain className="h-4 w-4 text-sage shrink-0" aria-hidden="true" />
                <div>
                  <p className="text-xs text-text-secondary leading-none">Tokens</p>
                  <p className="text-sm font-bold text-dark-brown mt-0.5">
                    {tokensUsed.toLocaleString()}
                  </p>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* ── Day cards ───────────────────────────────────────────── */}
      {studyPlan.length === 0 ? (
        <div className="rounded-2xl border border-beige bg-background px-6 py-10 text-center">
          <p className="text-sm text-text-secondary">
            The study plan schedule is empty. Try regenerating with a different topic.
          </p>
        </div>
      ) : (
        <ol className="flex flex-col gap-4" aria-label="Study plan schedule">
          {studyPlan.map((day, index) => (
            <DayCard
              key={day?.day ?? index}
              day={day}
              index={index}
              isCurrent={index === currentDayIndex}
              isCompleted={false}
              totalDays={studyPlan.length}
            />
          ))}
        </ol>
      )}

      {/* ── Footer note ─────────────────────────────────────────── */}
      <p className="text-xs text-center text-text-secondary/60 pb-2">
        Generated from your uploaded study material · Grounded in retrieved context · {modelUsed}
      </p>
    </div>
  );
}

/* ── Individual day card ────────────────────────────────────────────── */
interface DayCardProps {
  day: StudyPlanDay;
  index: number;
  isCurrent: boolean;
  isCompleted: boolean;
  totalDays: number;
}

function DayCard({ day, index, isCurrent, isCompleted, totalDays }: DayCardProps) {
  /* Safe extraction */
  const dayNum  = day?.day   ?? index + 1;
  const focus   = day?.focus ?? "";
  const tasks   = Array.isArray(day?.tasks) ? day.tasks.filter(Boolean) : [];

  return (
    <li
      className={clsx(
        "card-hover overflow-hidden",
        isCurrent && "ring-1 ring-terracotta/30"
      )}
      aria-label={`Day ${dayNum}: ${focus}`}
    >
      {/* Card header */}
      <div
        className={clsx(
          "flex items-center gap-3 border-b border-border px-5 py-4",
          isCompleted && "bg-ai-bg",
          isCurrent   && "bg-terracotta/[0.04]",
          !isCompleted && !isCurrent && "bg-background"
        )}
      >
        {/* Day number bubble */}
        <span
          className={clsx(
            "flex h-9 w-9 shrink-0 items-center justify-center rounded-full",
            "text-sm font-bold transition-colors",
            isCompleted && "bg-sage text-white",
            isCurrent   && "bg-terracotta text-white",
            !isCompleted && !isCurrent && "bg-beige/70 text-text-secondary"
          )}
          aria-hidden="true"
        >
          {isCompleted
            ? <CheckCircle2 className="h-4.5 w-4.5" />
            : dayNum
          }
        </span>

        {/* Day label + focus */}
        <div className="flex-1 min-w-0">
          <div className="flex flex-wrap items-baseline gap-2">
            <span
              className={clsx(
                "text-sm font-bold",
                isCompleted && "text-sage",
                isCurrent   && "text-dark-brown",
                !isCompleted && !isCurrent && "text-text-secondary"
              )}
            >
              Day {dayNum}
            </span>
            {focus && (
              <span
                className={clsx(
                  "text-sm truncate",
                  isCompleted && "text-sage/80",
                  isCurrent   && "font-semibold text-dark-brown",
                  !isCompleted && !isCurrent && "text-text-secondary"
                )}
              >
                {focus}
              </span>
            )}
          </div>

          {/* Task count sub-label */}
          <p className="text-xs text-text-secondary mt-0.5">
            {tasks.length} task{tasks.length !== 1 ? "s" : ""}
          </p>
        </div>

        {/* Status pill */}
        {isCurrent && (
          <span className="shrink-0 badge-terracotta">Today</span>
        )}
        {isCompleted && (
          <span className="shrink-0 badge-sage">Done</span>
        )}
        {!isCurrent && !isCompleted && (
          <span className="shrink-0 text-xs font-medium text-text-secondary/60 tabular-nums">
            {index + 1}/{totalDays}
          </span>
        )}
      </div>

      {/* Tasks list */}
      {tasks.length > 0 && (
        <ul
          className="flex flex-col divide-y divide-border/40 px-5"
          aria-label={`Tasks for Day ${dayNum}`}
        >
          {tasks.map((task, ti) => (
            <li
              key={ti}
              className="flex items-start gap-3 py-3"
            >
              {/* Task bullet */}
              <span
                className={clsx(
                  "mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-full",
                  "text-xs font-bold",
                  isCompleted && "bg-sage/15 text-sage",
                  isCurrent   && "bg-terracotta/10 text-terracotta",
                  !isCompleted && !isCurrent && "bg-beige/50 text-text-secondary"
                )}
                aria-hidden="true"
              >
                {isCompleted
                  ? <CheckCircle2 className="h-3 w-3" />
                  : ti + 1
                }
              </span>

              {/* Task text */}
              <p
                className={clsx(
                  "text-sm leading-relaxed flex-1",
                  isCompleted && "text-sage/80",
                  isCurrent   && "text-dark-brown",
                  !isCompleted && !isCurrent && "text-text-secondary"
                )}
              >
                {task}
              </p>
            </li>
          ))}
        </ul>
      )}

      {/* Empty tasks fallback */}
      {tasks.length === 0 && (
        <div className="px-5 py-4">
          <p className="text-xs text-text-secondary italic">No tasks specified for this day.</p>
        </div>
      )}
    </li>
  );
}
