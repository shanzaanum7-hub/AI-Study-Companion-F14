"use client";

/**
 * RetrievalSearch
 * ────────────────
 * Step 2 of the workflow: user enters a topic/question, hits "Find Relevant
 * Content", the frontend calls POST /api/retrieve.
 *
 * States:
 *   idle       — input ready, button enabled (when doc is processed)
 *   searching  — loading spinner, input disabled
 *   disabled   — document not yet processed (button disabled + tooltip)
 *
 * Props:
 *   onSearch       — called with the query string when the user submits
 *   isLoading      — true while the API call is in flight
 *   isEnabled      — false until a document has been successfully indexed
 *   error          — AppError to display below the input
 */

import { useState, useRef } from "react";
import { Search, Loader2, AlertCircle, BookOpen } from "lucide-react";
import clsx from "clsx";
import type { AppError } from "@/lib/api/types";

const EXAMPLE_QUERIES = [
  "CPU Scheduling algorithms",
  "Process synchronisation and deadlock",
  "Memory management techniques",
  "TCP connection lifecycle",
  "Database normalisation",
];

interface RetrievalSearchProps {
  onSearch: (query: string) => void;
  isLoading?: boolean;
  isEnabled?: boolean;
  error?: AppError | null;
}

export default function RetrievalSearch({
  onSearch,
  isLoading = false,
  isEnabled = false,
  error = null,
}: RetrievalSearchProps) {
  const [query, setQuery]   = useState("");
  const inputRef            = useRef<HTMLInputElement>(null);

  const canSubmit = isEnabled && !isLoading && query.trim().length >= 2;

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!canSubmit) return;
    onSearch(query.trim());
  }

  function fillExample(example: string) {
    setQuery(example);
    inputRef.current?.focus();
  }

  return (
    <div className="flex flex-col gap-6">

      {/* ── Section label + heading ──────────────────────────── */}
      <div>
        <p className="label-sm text-terracotta mb-1.5">Step 2 · Retrieval</p>
        <h2 className="heading-2 text-dark-brown">Find What You Need</h2>
        <p className="body-base mt-2 max-w-lg">
          Enter a topic or question to retrieve the most relevant parts of
          your uploaded material using semantic AI search.
        </p>
      </div>

      {/* ── Search form ─────────────────────────────────────── */}
      <form
        onSubmit={handleSubmit}
        className="flex flex-col gap-3"
        aria-label="Semantic search form"
      >
        {/* Input row */}
        <div className="relative flex items-center">
          {/* Leading icon */}
          <span
            className={clsx(
              "absolute left-4 flex h-5 w-5 items-center justify-center",
              "pointer-events-none transition-colors",
              isEnabled ? "text-sage" : "text-beige"
            )}
            aria-hidden="true"
          >
            {isLoading
              ? <Loader2 className="h-5 w-5 animate-spin text-terracotta" />
              : <Search className="h-5 w-5" />
            }
          </span>

          {/* Text input */}
          <input
            ref={inputRef}
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => { if (e.key === "Enter") handleSubmit(e as unknown as React.FormEvent); }}
            disabled={!isEnabled || isLoading}
            placeholder={
              isEnabled
                ? "e.g. Process Scheduling, TCP Connection, Deadlock…"
                : "Upload and process a document first"
            }
            maxLength={500}
            className={clsx(
              "w-full rounded-xl border py-3.5 pl-12 pr-4 text-sm outline-none",
              "transition-all duration-200 bg-card",
              "placeholder:text-text-secondary/50",
              isEnabled && !isLoading
                ? "border-beige text-dark-brown hover:border-sage focus:border-terracotta focus:ring-2 focus:ring-terracotta/15"
                : "border-beige/60 text-text-secondary cursor-not-allowed bg-background",
              error && "border-terracotta/50 focus:border-terracotta"
            )}
            aria-label="Search query"
            aria-disabled={!isEnabled || isLoading}
            autoComplete="off"
            spellCheck="false"
          />

          {/* Character count (subtle) */}
          {query.length > 0 && isEnabled && (
            <span className="absolute right-4 text-xs text-text-secondary/50 pointer-events-none">
              {query.length}/500
            </span>
          )}
        </div>

        {/* Submit button */}
        <button
          type="submit"
          disabled={!canSubmit}
          className="btn-primary w-full justify-center py-3.5 text-base"
          aria-busy={isLoading}
          aria-disabled={!canSubmit}
        >
          {isLoading
            ? <><Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" /> Searching…</>
            : <><Search className="h-4 w-4" aria-hidden="true" /> Find Relevant Content</>
          }
        </button>

        {/* Disabled notice */}
        {!isEnabled && (
          <div className="flex items-center gap-2.5 rounded-xl border border-beige bg-background px-4 py-3">
            <BookOpen className="h-4 w-4 text-beige shrink-0" aria-hidden="true" />
            <p className="text-xs text-text-secondary">
              Process a document first — then search for any topic within it.
            </p>
          </div>
        )}
      </form>

      {/* ── Error display ────────────────────────────────────── */}
      {error && (
        <div
          role="alert"
          className="flex items-start gap-3 rounded-xl border border-terracotta/25
                     bg-terracotta/6 px-4 py-3"
        >
          <AlertCircle
            className="h-4 w-4 text-terracotta shrink-0 mt-0.5"
            aria-hidden="true"
          />
          <div>
            <p className="text-sm font-semibold text-terracotta">
              {error.message}
            </p>
            {error.details && (
              <p className="text-xs text-text-secondary mt-0.5">{error.details}</p>
            )}
          </div>
        </div>
      )}

      {/* ── Example query chips ─────────────────────────────── */}
      {isEnabled && !isLoading && (
        <div className="flex flex-col gap-2">
          <p className="text-xs font-semibold uppercase tracking-wider text-text-secondary">
            Try an example
          </p>
          <div
            className="flex flex-wrap gap-2"
            role="list"
            aria-label="Example search queries"
          >
            {EXAMPLE_QUERIES.map((ex) => (
              <button
                key={ex}
                type="button"
                role="listitem"
                onClick={() => fillExample(ex)}
                className={clsx(
                  "rounded-full border border-beige bg-card px-3.5 py-1.5",
                  "text-xs font-medium text-text-secondary",
                  "transition-all duration-150 hover:border-sage hover:bg-ai-bg hover:text-dark-brown",
                  "focus-visible:outline focus-visible:outline-2 focus-visible:outline-terracotta",
                  query === ex && "border-terracotta/40 bg-terracotta/6 text-terracotta"
                )}
                aria-pressed={query === ex}
              >
                {ex}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
