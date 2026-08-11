"use client";

import { useState } from "react";
import DocumentIllustration from "./illustrations/DocumentIllustration";
import ProcessingIllustration from "./illustrations/ProcessingIllustration";
import UploadCard from "./UploadCard";
import ProcessingStatus from "./ProcessingStatus";
import DocumentStats from "./DocumentStats";
import { uploadDocument } from "@/lib/api/documents";
import type {
  AppError,
  DocumentStats as DocumentStatsType,
  ProcessingStep,
  UploadResponse,
} from "@/lib/api/types";

interface UploadSectionProps {
  /** Called when the document is fully processed and ready for retrieval */
  onDocumentReady: (doc: UploadResponse) => void;
}

type LocalStage = "idle" | "uploading" | "processing" | "done" | "error";

const INITIAL_STEPS: ProcessingStep[] = [
  { id: "upload",     label: "Document uploaded",       status: "pending" },
  { id: "extract",    label: "Extracting text",         status: "pending" },
  { id: "chunk",      label: "Creating chunks",         status: "pending" },
  { id: "embed",      label: "Generating embeddings",   status: "pending" },
  { id: "store",      label: "Storing in Qdrant",       status: "pending" },
];

/** Simulate the backend pipeline steps — in production these reflect real
 *  backend events. Since the backend processes synchronously on upload,
 *  we animate the steps over a realistic timeline to give visual feedback. */
async function runSimulatedPipeline(
  setSteps: React.Dispatch<React.SetStateAction<ProcessingStep[]>>,
  signal: AbortSignal
): Promise<void> {
  const timings = [0, 600, 1200, 1900, 2700]; // ms offset per step
  const stepIds = ["upload", "extract", "chunk", "embed", "store"];

  for (let i = 0; i < stepIds.length; i++) {
    await new Promise<void>((resolve) => {
      const t = setTimeout(resolve, i === 0 ? 0 : 700);
      signal.addEventListener("abort", () => { clearTimeout(t); resolve(); });
    });
    if (signal.aborted) return;

    setSteps((prev) =>
      prev.map((s, idx) => {
        if (idx < i)  return { ...s, status: "completed" };
        if (idx === i) return { ...s, status: "processing" };
        return s;
      })
    );

    await new Promise<void>((resolve) => {
      const t = setTimeout(resolve, 800);
      signal.addEventListener("abort", () => { clearTimeout(t); resolve(); });
    });
    if (signal.aborted) return;

    setSteps((prev) =>
      prev.map((s, idx) =>
        idx === i ? { ...s, status: "completed" } : s
      )
    );
  }

  void timings; // suppress unused warning
}

export default function UploadSection({ onDocumentReady }: UploadSectionProps) {
  const [localStage,    setLocalStage]    = useState<LocalStage>("idle");
  const [uploadPct,     setUploadPct]     = useState(0);
  const [steps,         setSteps]         = useState<ProcessingStep[]>(INITIAL_STEPS);
  const [error,         setError]         = useState<AppError | null>(null);
  const [docStats,      setDocStats]      = useState<DocumentStatsType | null>(null);
  const [uploadResponse, setUploadResponse] = useState<UploadResponse | null>(null);

  const isLoading  = localStage === "uploading" || localStage === "processing";
  const isProcessed = localStage === "done";

  async function handleProcess(file: File) {
    setError(null);
    setLocalStage("uploading");
    setUploadPct(0);
    setSteps(INITIAL_STEPS);

    /* ── Step 1: Upload to FastAPI ─────────────────────────────── */
    const { data, error: uploadErr } = await uploadDocument(file, (pct) => {
      setUploadPct(pct);
    });

    if (uploadErr || !data) {
      setError(uploadErr ?? { code: "UPLOAD", message: "Upload failed." });
      setLocalStage("error");
      setSteps((prev) =>
        prev.map((s, i) => (i === 0 ? { ...s, status: "failed" } : s))
      );
      return;
    }

    setUploadResponse(data);

    /* ── Step 2: Animate the pipeline ──────────────────────────── */
    setLocalStage("processing");
    const ac = new AbortController();
    await runSimulatedPipeline(setSteps, ac.signal);

    /* ── Step 3: Done ──────────────────────────────────────────── */
    setLocalStage("done");
    setDocStats({
      filename:   data.filename,
      fileType:   file.name.endsWith(".txt") ? "TXT" : "PDF",
      fileSizeMb: file.size / (1024 * 1024),
      documentId: data.document_id,
      status:     data.status,
    });
    onDocumentReady(data);
  }

  const cardStage: "idle" | "uploading" | "processing" =
    localStage === "uploading"  ? "uploading"  :
    localStage === "processing" ? "processing" : "idle";

  return (
    <section
      id="upload"
      className="section bg-background"
      aria-labelledby="upload-heading"
    >
      <div className="container-main">

        {/* ── Section heading ────────────────────────────────────── */}
        <div className="mb-10 md:mb-14 text-center">
          <p className="label-sm text-terracotta mb-2">
            AI STUDY COMPANION · STEP 1
          </p>
          <h2 className="heading-1 text-dark-brown" id="upload-heading">
            Upload Your Study Material
          </h2>
          <p className="body-lg mx-auto mt-3 max-w-xl">
            Upload a syllabus, lecture notes, or any study document. The AI
            engine will extract, chunk, embed, and index it — ready for
            intelligent retrieval.
          </p>
        </div>

        {/* ── Two-column layout ──────────────────────────────────── */}
        <div className="grid grid-cols-1 gap-8 lg:grid-cols-2 lg:gap-14 items-start">

          {/* Left: upload card + status + stats */}
          <div className="flex flex-col gap-6 animate-slide-up">
            <UploadCard
              onProcess={handleProcess}
              uploadProgress={uploadPct}
              isLoading={isLoading}
              stage={cardStage}
              error={error}
              isProcessed={isProcessed}
            />

            {/* Processing steps (show once upload is accepted) */}
            {(localStage === "processing" || localStage === "done" || localStage === "error") && (
              <div className="animate-fade-in">
                <ProcessingStatus steps={steps} />
              </div>
            )}

            {/* Document stats (show after done) */}
            {localStage === "done" && docStats && (
              <div className="animate-fade-in animation-delay-300">
                <DocumentStats stats={docStats} />
              </div>
            )}
          </div>

          {/* Right: illustration — switches from static to pipeline when processing */}
          <div className="flex items-center justify-center lg:justify-end animate-fade-in animation-delay-200">
            {localStage === "idle" || localStage === "error" ? (
              <div className="w-full max-w-sm">
                <DocumentIllustration />
                {/* Caption */}
                <p className="text-center text-xs text-text-secondary mt-4 leading-relaxed max-w-xs mx-auto">
                  Your document is split into meaningful chunks, converted to
                  vector embeddings, and stored in Qdrant for fast semantic
                  retrieval.
                </p>
              </div>
            ) : (
              <div className="w-full max-w-[460px]">
                <ProcessingIllustration />
                <p className="text-center text-xs text-text-secondary mt-3 leading-relaxed">
                  Text is extracted, split into chunks, embedded as vectors,
                  and stored in Qdrant for semantic search.
                </p>
              </div>
            )}
          </div>
        </div>

      </div>
    </section>
  );
}
