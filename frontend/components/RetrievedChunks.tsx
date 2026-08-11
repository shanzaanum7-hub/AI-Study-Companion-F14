"use client";

/**
 * RetrievedChunks
 * ────────────────
 * Renders the ranked list of text chunks returned by POST /api/retrieve.
 *
 * Each chunk is displayed as an elegant reading card showing:
 *   - Rank number + RELEVANT badge
 *   - Relevance score bar + numeric score
 *   - Full text content
 *   - Source document ID (truncated) + optional page number
 *
 * No raw vector data is shown. The design should feel like reading
 * useful study material, not a developer console.
 */

import { FileText, Hash, BookOpen } from "lucide-react";
import clsx from "clsx";
import type { SimpleRetrieveResult, SimpleRetrieveResponse } from "@/lib/api/types";

/* ── Score → colour + label ─────────────────────────────────────────── */
function scoreLabel(score: number): { label: string; color: string } {
  if (score >= 0.90) return { label: "Very High",  color: "text-sage font-semibold" };
  if (score >= 0.75) return { label: "High",       color: "text-sage" };
  if (score >= 0.60) return { label: "Moderate",   color: "text-text-secondary" };
  return               { label: "Low",        color: "text-beige" };
}

/* ── Short document ID display ──────────────────────────────────────── */
function shortId(id: string | null): string {
  if (!id) return "—";
  return id.length > 16 ? `…${id.slice(-14)}` : id;
}

interface RetrievedChunksProps {
  response: SimpleRetrieveResponse;
  /** Allow parent to scroll to this section */
  sectionRef?: React.RefObject<HTMLDivElement>;
}

export default function RetrievedChunks({
  response,
  sectionRef,
}: RetrievedChunksProps) {
  const { query, results } = response;

  return (
    <div ref={sectionRef} className="flex flex-col gap-5">

      {/* ── Section header ────────────────────────────────────── */}
      <div className="flex flex-col gap-1 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="label-sm text-terracotta mb-1">Retrieval Results</p>
          <h3 className="heading-3 text-dark-brown">Relevant Study Material</h3>
          <p className="body-base mt-1">
            Showing the{" "}
            <span className="font-semibold text-dark-brown">{results.length}</span>{" "}
            most relevant chunk{results.length !== 1 ? "s" : ""} for{" "}
            <span className="font-semibold text-dark-brown">
              &ldquo;{query}&rdquo;
            </span>
          </p>
        </div>

        {/* Total count badge */}
        <span className="badge-sage self-start sm:self-auto shrink-0">
          <Hash className="h-3 w-3" aria-hidden="true" />
          {results.length} result{results.length !== 1 ? "s" : ""}
        </span>
      </div>

      {/* ── Chunk cards ───────────────────────────────────────── */}
      <ol className="flex flex-col gap-4" aria-label="Retrieved content chunks">
        {results.map((chunk, index) => (
          <ChunkCard key={chunk.chunk_id ?? index} chunk={chunk} rank={index + 1} />
        ))}
      </ol>
    </div>
  );
}

/* ── Individual chunk card ──────────────────────────────────────────── */
function ChunkCard({
  chunk,
  rank,
}: {
  chunk: SimpleRetrieveResult;
  rank: number;
}) {
  const score      = Math.max(0, Math.min(1, chunk.score));
  const scorePct   = Math.round(score * 100);
  const { label: scoreText, color: scoreColor } = scoreLabel(score);
  const isTopResult = rank === 1;

  return (
    <li
      className={clsx(
        "card-hover group flex flex-col gap-0 overflow-hidden",
        isTopResult && "ring-1 ring-sage/40"
      )}
      aria-label={`Result ${rank}: relevance score ${scorePct}%`}
    >
      {/* Card header ─────────────────────────────────────────── */}
      <div
        className={clsx(
          "flex items-center justify-between gap-3 px-5 py-3.5 border-b border-border",
          isTopResult ? "bg-ai-bg" : "bg-background"
        )}
      >
        <div className="flex items-center gap-2.5 min-w-0">
          {/* Rank bubble */}
          <span
            className={clsx(
              "flex h-6 w-6 shrink-0 items-center justify-center rounded-full",
              "text-xs font-bold",
              isTopResult
                ? "bg-sage text-white"
                : "bg-beige text-text-secondary"
            )}
            aria-hidden="true"
          >
            {rank}
          </span>

          {/* RELEVANT badge */}
          <span
            className={clsx(
              "inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-xs font-semibold",
              isTopResult
                ? "bg-sage/15 text-sage"
                : "bg-beige/60 text-text-secondary"
            )}
          >
            <span
              className={clsx(
                "h-1.5 w-1.5 rounded-full",
                isTopResult ? "bg-sage" : "bg-beige"
              )}
              aria-hidden="true"
            />
            RELEVANT
          </span>
        </div>

        {/* Score */}
        <div className="flex items-center gap-2 shrink-0">
          <span
            className={clsx("text-sm tabular-nums", scoreColor)}
            aria-label={`Cosine similarity score ${score.toFixed(2)}`}
          >
            {score.toFixed(2)}
          </span>
          <span className="text-xs text-text-secondary hidden sm:inline">
            {scoreText}
          </span>
        </div>
      </div>

      {/* Score bar ────────────────────────────────────────────── */}
      <div
        className="h-1 w-full bg-beige/40"
        role="presentation"
        aria-hidden="true"
      >
        <div
          className={clsx(
            "h-full rounded-r-full transition-all duration-500",
            isTopResult ? "bg-sage" : "bg-beige"
          )}
          style={{ width: `${scorePct}%` }}
        />
      </div>

      {/* Text content ─────────────────────────────────────────── */}
      <div className="px-5 py-4">
        <p
          className="text-sm leading-relaxed text-dark-brown"
          style={{
            display: "-webkit-box",
            WebkitLineClamp: 8,
            WebkitBoxOrient: "vertical",
            overflow: "hidden",
          }}
        >
          {chunk.text}
        </p>
      </div>

      {/* Card footer ──────────────────────────────────────────── */}
      <div className="flex flex-wrap items-center gap-3 border-t border-border bg-background px-5 py-3">
        {/* Source document */}
        {chunk.document_id && (
          <span className="flex items-center gap-1.5 text-xs text-text-secondary">
            <FileText className="h-3.5 w-3.5 text-beige shrink-0" aria-hidden="true" />
            <span className="font-medium">Source:</span>
            <span className="font-mono text-[11px]">{shortId(chunk.document_id)}</span>
          </span>
        )}

        {/* Page number */}
        {chunk.page_number != null && (
          <span className="flex items-center gap-1.5 text-xs text-text-secondary">
            <BookOpen className="h-3.5 w-3.5 text-beige shrink-0" aria-hidden="true" />
            <span className="font-medium">Page {chunk.page_number}</span>
          </span>
        )}

        {/* Chunk ID */}
        {chunk.chunk_id && (
          <span className="flex items-center gap-1.5 text-xs text-text-secondary ml-auto">
            <Hash className="h-3 w-3 text-beige shrink-0" aria-hidden="true" />
            <span className="font-mono text-[11px] opacity-60">
              {chunk.chunk_id.slice(0, 12)}
            </span>
          </span>
        )}
      </div>
    </li>
  );
}
