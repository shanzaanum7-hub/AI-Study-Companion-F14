"use client";

import { FileText, Layers, Cpu, Database, CheckCircle2 } from "lucide-react";
import type { DocumentStats as DocumentStatsType } from "@/lib/api/types";

interface DocumentStatsProps {
  stats: DocumentStatsType;
  numChunks?: number;
}

export default function DocumentStats({ stats, numChunks }: DocumentStatsProps) {
  const fields = [
    {
      icon: <FileText className="h-4 w-4 text-terracotta" aria-hidden="true" />,
      label: "Document",
      value: stats.filename,
      sub: `${stats.fileType} · ${stats.fileSizeMb.toFixed(2)} MB`,
    },
    {
      icon: <Layers className="h-4 w-4 text-sage" aria-hidden="true" />,
      label: "Chunks",
      value: numChunks !== undefined ? String(numChunks) : "—",
      sub: numChunks ? "text segments indexed" : "processing…",
    },
    {
      icon: <Cpu className="h-4 w-4 text-sage" aria-hidden="true" />,
      label: "Embeddings",
      value: "Generated",
      sub: "Gemini text-embedding-004",
    },
    {
      icon: <Database className="h-4 w-4 text-dark-brown" aria-hidden="true" />,
      label: "Vector Database",
      value: "Qdrant",
      sub: "study_notes collection",
    },
  ];

  return (
    <div className="card overflow-hidden">
      {/* Header */}
      <div className="flex items-center gap-2 bg-ai-bg border-b border-border px-5 py-3.5">
        <CheckCircle2 className="h-4 w-4 text-sage" aria-hidden="true" />
        <h3 className="text-sm font-semibold text-dark-brown">Document Indexed</h3>
      </div>

      {/* Stats grid */}
      <dl className="divide-y divide-border">
        {fields.map((f) => (
          <div key={f.label} className="flex items-center gap-4 px-5 py-3.5">
            <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-background border border-border">
              {f.icon}
            </span>
            <div className="flex-1 min-w-0">
              <dt className="text-xs font-semibold uppercase tracking-wider text-text-secondary">
                {f.label}
              </dt>
              <dd className="text-sm font-semibold text-dark-brown truncate mt-0.5">
                {f.value}
              </dd>
              {f.sub && (
                <dd className="text-xs text-text-secondary">{f.sub}</dd>
              )}
            </div>
          </div>
        ))}
      </dl>
    </div>
  );
}
