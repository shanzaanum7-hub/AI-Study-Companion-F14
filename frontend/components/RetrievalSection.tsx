"use client";

/**
 * RetrievalSection
 * ─────────────────
 * Complete Step 2 section: Search input on the left, illustration on the
 * right; results rendered full-width below after a successful query.
 *
 * Stages managed here:
 *   idle       — search form + illustration visible
 *   searching  — spinner on the button, illustration stays
 *   retrieved  — results appear below; illustration replaced by a compact
 *                "semantic retrieval" visual summary
 *   error      — error banner in the search form
 *
 * Props:
 *   isEnabled        — false until a document has been indexed
 *   documentId       — passed to the API to scope the search (optional)
 *   onResultsReady   — called with the query string when results arrive
 */

import { useRef, useState } from "react";
import RetrievalSearch from "./RetrievalSearch";
import RetrievedChunks from "./RetrievedChunks";
import RetrievalIllustration from "./illustrations/RetrievalIllustration";
import { retrieveChunks } from "@/lib/api/retrieval";
import type {
  AppError,
  SimpleRetrieveResponse,
} from "@/lib/api/types";

interface RetrievalSectionProps {
  isEnabled: boolean;
  documentId?: string;
  onResultsReady?: (query: string) => void;
}

export default function RetrievalSection({
  isEnabled,
  documentId,
  onResultsReady,
}: RetrievalSectionProps) {
  const [isSearching, setIsSearching] = useState(false);
  const [error,       setError]       = useState<AppError | null>(null);
  const [response,    setResponse]    = useState<SimpleRetrieveResponse | null>(null);

  const resultsRef = useRef<HTMLDivElement>(null);

  async function handleSearch(query: string) {
    setError(null);
    setIsSearching(true);
    setResponse(null);

    const { data, error: apiErr } = await retrieveChunks({
      query,
      top_k: 5,
      document_id: documentId,
    });

    setIsSearching(false);

    if (apiErr || !data) {
      setError(apiErr ?? { code: "RETRIEVE", message: "Search failed." });
      return;
    }

    setResponse(data);
    onResultsReady?.(query);

    // Scroll to results smoothly after a short paint delay
    setTimeout(() => {
      resultsRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
    }, 100);
  }

  const hasResults = response !== null && response.results.length > 0;

  return (
    <section
      id="retrieval"
      className="section bg-off-white border-t border-border"
      aria-labelledby="retrieval-heading"
    >
      <div className="container-main">

        {/* ── Section heading ────────────────────────────────────── */}
        <div className="mb-10 md:mb-14 text-center">
          <p className="label-sm text-terracotta mb-2">
            AI STUDY COMPANION · STEP 2
          </p>
          <h2
            className="heading-1 text-dark-brown"
            id="retrieval-heading"
          >
            Find What You Need
          </h2>
          <p className="body-lg mx-auto mt-3 max-w-xl">
            Enter any topic or question. The AI engine embeds your query,
            searches Qdrant with cosine similarity, and surfaces the most
            relevant passages from your document.
          </p>
        </div>

        {/* ── Two-column: search form + illustration ─────────────── */}
        <div className="grid grid-cols-1 gap-10 lg:grid-cols-2 lg:gap-14 items-start mb-12">

          {/* Left: search controls */}
          <div className="animate-slide-up">
            <div className="card p-6 md:p-8">
              <RetrievalSearch
                onSearch={handleSearch}
                isLoading={isSearching}
                isEnabled={isEnabled}
                error={error}
              />
            </div>

            {/* How it works note — visible when not yet enabled */}
            {!isEnabled && (
              <div className="mt-4 flex items-start gap-3 rounded-xl border border-beige
                              bg-background px-4 py-3.5">
                <span
                  className="flex h-8 w-8 shrink-0 items-center justify-center
                             rounded-lg bg-beige/50 text-text-secondary text-sm font-bold"
                  aria-hidden="true"
                >
                  2
                </span>
                <p className="text-sm text-text-secondary leading-relaxed">
                  This step unlocks once your document has been uploaded and
                  indexed in Step 1.
                </p>
              </div>
            )}
          </div>

          {/* Right: illustration */}
          <div
            className="flex flex-col items-center justify-start gap-4
                       animate-fade-in animation-delay-200"
          >
            <RetrievalIllustration />

            {/* Caption beneath illustration */}
            <p className="text-center text-xs text-text-secondary leading-relaxed max-w-xs">
              Your query is converted to a 768-dim Gemini vector and matched
              against indexed chunks using cosine similarity in Qdrant.
            </p>

            {/* Inline pipeline legend */}
            <div className="flex items-center gap-2 flex-wrap justify-center">
              {[
                { label: "Query embedding", color: "#B9684E" },
                { label: "Qdrant search",   color: "#87977B" },
                { label: "Top-5 chunks",    color: "#40352F" },
              ].map((item, i) => (
                <span key={item.label} className="flex items-center gap-1.5 text-xs text-text-secondary">
                  {i > 0 && (
                    <span className="text-beige" aria-hidden="true">→</span>
                  )}
                  <span
                    className="h-2 w-2 rounded-full shrink-0"
                    style={{ backgroundColor: item.color }}
                    aria-hidden="true"
                  />
                  {item.label}
                </span>
              ))}
            </div>
          </div>
        </div>

        {/* ── Results (full-width, below the two columns) ─────────── */}
        {hasResults && (
          <div
            className="animate-slide-up border-t border-border pt-10"
            ref={resultsRef}
          >
            {/* "Semantic search complete" status banner */}
            <div
              role="status"
              aria-live="polite"
              className="mb-6 flex items-center gap-3 rounded-xl border border-sage/25
                         bg-ai-bg px-5 py-3.5"
            >
              <span
                className="flex h-8 w-8 shrink-0 items-center justify-center
                           rounded-full bg-sage/20"
                aria-hidden="true"
              >
                {/* Magnifier-check icon built from Lucide primitives */}
                <svg
                  viewBox="0 0 24 24" fill="none"
                  className="h-4 w-4 text-sage"
                  stroke="currentColor" strokeWidth="2"
                  strokeLinecap="round" strokeLinejoin="round"
                >
                  <circle cx="11" cy="11" r="8" />
                  <path d="M21 21l-4.35-4.35" />
                  <path d="M8 11l2 2 4-4" />
                </svg>
              </span>
              <div>
                <p className="text-sm font-semibold text-dark-brown">
                  Semantic search complete
                </p>
                <p className="text-xs text-text-secondary">
                  {response.results.length} chunk
                  {response.results.length !== 1 ? "s" : ""} retrieved for &ldquo;
                  {response.query}&rdquo;
                </p>
              </div>
            </div>

            <RetrievedChunks response={response} />
          </div>
        )}

        {/* Empty result state */}
        {response !== null && response.results.length === 0 && (
          <div
            role="status"
            className="mt-8 flex flex-col items-center gap-3 rounded-2xl border
                       border-beige bg-background px-6 py-12 text-center"
          >
            <span
              className="flex h-12 w-12 items-center justify-center rounded-full bg-beige/50"
              aria-hidden="true"
            >
              <svg
                viewBox="0 0 24 24" fill="none"
                className="h-6 w-6 text-text-secondary"
                stroke="currentColor" strokeWidth="1.5"
                strokeLinecap="round" strokeLinejoin="round"
              >
                <circle cx="11" cy="11" r="8" />
                <path d="M21 21l-4.35-4.35" />
              </svg>
            </span>
            <p className="text-sm font-semibold text-dark-brown">No results found</p>
            <p className="text-xs text-text-secondary max-w-sm">
              No matching content was found for &ldquo;{response.query}&rdquo;.
              Try a broader topic or make sure the relevant content is in your
              uploaded document.
            </p>
          </div>
        )}

      </div>
    </section>
  );
}
