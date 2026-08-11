"use client";

import { useCallback, useRef, useState } from "react";
import {
  FileText,
  UploadCloud,
  X,
  AlertCircle,
  CheckCircle2,
  Loader2,
} from "lucide-react";
import clsx from "clsx";
import type { AppError, UploadedFile } from "@/lib/api/types";

interface UploadCardProps {
  /** Called when the user clicks "Process Document" */
  onProcess: (file: File) => void;
  /** Upload progress 0-100, shown only while uploading */
  uploadProgress?: number;
  /** Whether an upload/process is currently in flight */
  isLoading?: boolean;
  /** Stage label shown in the button */
  stage?: "idle" | "uploading" | "processing";
  /** Error to display inside the card */
  error?: AppError | null;
  /** Whether the document was already processed (success state) */
  isProcessed?: boolean;
}

const ALLOWED_TYPES = ["application/pdf", "text/plain"];
const ALLOWED_EXTS  = [".pdf", ".txt"];
const MAX_SIZE_MB   = 20;

function formatBytes(bytes: number): string {
  if (bytes < 1024)        return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
}

function fileTypeLabel(mime: string): string {
  if (mime === "application/pdf") return "PDF";
  if (mime === "text/plain")      return "TXT";
  return mime.split("/")[1]?.toUpperCase() ?? "FILE";
}

export default function UploadCard({
  onProcess,
  uploadProgress = 0,
  isLoading = false,
  stage = "idle",
  error = null,
  isProcessed = false,
}: UploadCardProps) {
  const [selectedFile, setSelectedFile]   = useState<UploadedFile | null>(null);
  const [dragActive, setDragActive]       = useState(false);
  const [validationErr, setValidationErr] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  /* ── Validation ─────────────────────────────────────────────── */
  function validate(file: File): string | null {
    if (!ALLOWED_TYPES.includes(file.type)) {
      return `Unsupported file type. Please upload a PDF or TXT file.`;
    }
    if (file.size > MAX_SIZE_MB * 1024 * 1024) {
      return `File too large. Maximum allowed size is ${MAX_SIZE_MB} MB.`;
    }
    return null;
  }

  function pickFile(file: File) {
    const err = validate(file);
    if (err) { setValidationErr(err); return; }
    setValidationErr(null);
    setSelectedFile({ file, name: file.name, size: file.size, type: file.type });
  }

  /* ── Drag handlers ──────────────────────────────────────────── */
  const onDragOver  = useCallback((e: React.DragEvent) => { e.preventDefault(); setDragActive(true);  }, []);
  const onDragLeave = useCallback((e: React.DragEvent) => { e.preventDefault(); setDragActive(false); }, []);
  const onDrop      = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragActive(false);
    const file = e.dataTransfer.files[0];
    if (file) pickFile(file);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  /* ── Browse handler ─────────────────────────────────────────── */
  function onFileChange(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (file) pickFile(file);
    e.target.value = "";
  }

  function removeFile() {
    setSelectedFile(null);
    setValidationErr(null);
  }

  /* ── Submit ─────────────────────────────────────────────────── */
  function handleProcess() {
    if (!selectedFile || isLoading) return;
    onProcess(selectedFile.file);
  }

  const canProcess = !!selectedFile && !isLoading && !isProcessed;

  /* ── Button label ───────────────────────────────────────────── */
  function buttonLabel() {
    if (stage === "uploading")  return "Uploading…";
    if (stage === "processing") return "Processing…";
    if (isProcessed)            return "Document Processed";
    return "Process Document";
  }

  const displayError = validationErr ?? error?.message ?? null;

  return (
    <div className="card p-6 md:p-8 flex flex-col gap-6">

      {/* ── Header ──────────────────────────────────────────────── */}
      <div>
        <p className="label-sm text-terracotta mb-1">Step 1</p>
        <h2 className="heading-3 text-dark-brown">Upload Your Study Material</h2>
        <p className="body-base mt-1.5">
          Upload a syllabus or study-notes file to build your personalised
          study context.
        </p>
      </div>

      {/* ── Supported formats ───────────────────────────────────── */}
      <div className="flex flex-wrap gap-2">
        {["PDF", "TXT"].map((fmt) => (
          <span key={fmt} className="badge-brown gap-1">
            <FileText className="h-3.5 w-3.5" aria-hidden="true" />
            {fmt}
          </span>
        ))}
        <span className="text-xs text-text-secondary self-center pl-1">
          Max {MAX_SIZE_MB} MB
        </span>
      </div>

      {/* ── Drop zone ───────────────────────────────────────────── */}
      {!selectedFile ? (
        <button
          type="button"
          className={clsx(
            "relative flex flex-col items-center justify-center gap-3 rounded-2xl border-2",
            "border-dashed px-6 py-10 text-center transition-all duration-200 w-full",
            "focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-terracotta",
            dragActive
              ? "border-terracotta bg-terracotta/5 scale-[1.01]"
              : "border-beige bg-background hover:border-sage hover:bg-ai-bg"
          )}
          onClick={() => inputRef.current?.click()}
          onDragOver={onDragOver}
          onDragLeave={onDragLeave}
          onDrop={onDrop}
          aria-label="Upload area — click to browse, or drag and drop a file"
        >
          <span
            className={clsx(
              "flex h-14 w-14 items-center justify-center rounded-2xl transition-colors",
              dragActive ? "bg-terracotta/15" : "bg-beige/60"
            )}
          >
            <UploadCloud
              className={clsx(
                "h-7 w-7 transition-colors",
                dragActive ? "text-terracotta" : "text-sage"
              )}
              aria-hidden="true"
            />
          </span>

          <span className="flex flex-col gap-1">
            <span className="text-sm font-semibold text-dark-brown">
              {dragActive ? "Drop your file here" : "Drop your PDF or TXT file here"}
            </span>
            <span className="text-xs text-text-secondary">
              or{" "}
              <span className="text-terracotta font-semibold underline underline-offset-2">
                browse from your computer
              </span>
            </span>
          </span>

          <input
            ref={inputRef}
            type="file"
            accept={ALLOWED_EXTS.join(",")}
            onChange={onFileChange}
            className="sr-only"
            aria-label="File input"
            tabIndex={-1}
          />
        </button>
      ) : (
        /* ── Selected file card ───────────────────────────────── */
        <div className="rounded-2xl border border-beige bg-background px-5 py-4 flex items-center gap-4">
          {/* File type icon */}
          <span
            className={clsx(
              "flex h-11 w-11 shrink-0 items-center justify-center rounded-xl text-xs font-bold text-white",
              selectedFile.type === "application/pdf" ? "bg-terracotta" : "bg-sage"
            )}
            aria-hidden="true"
          >
            {fileTypeLabel(selectedFile.type)}
          </span>

          {/* Info */}
          <div className="flex-1 min-w-0">
            <p className="text-sm font-semibold text-dark-brown truncate">
              {selectedFile.name}
            </p>
            <p className="text-xs text-text-secondary mt-0.5">
              {formatBytes(selectedFile.size)}
            </p>
          </div>

          {/* Remove */}
          {!isLoading && !isProcessed && (
            <button
              onClick={removeFile}
              className="shrink-0 flex h-8 w-8 items-center justify-center rounded-lg
                         text-text-secondary hover:bg-beige hover:text-terracotta
                         transition-colors focus-visible:outline focus-visible:outline-2
                         focus-visible:outline-terracotta"
              aria-label={`Remove ${selectedFile.name}`}
            >
              <X className="h-4 w-4" />
            </button>
          )}

          {isProcessed && (
            <CheckCircle2 className="h-5 w-5 text-sage shrink-0" aria-hidden="true" />
          )}
        </div>
      )}

      {/* ── Upload progress bar ─────────────────────────────────── */}
      {stage === "uploading" && (
        <div role="progressbar" aria-valuenow={uploadProgress} aria-valuemin={0} aria-valuemax={100} aria-label="Upload progress">
          <div className="flex items-center justify-between mb-1.5">
            <span className="text-xs font-medium text-text-secondary">Uploading…</span>
            <span className="text-xs font-semibold text-terracotta">{uploadProgress}%</span>
          </div>
          <div className="h-1.5 w-full rounded-full bg-beige overflow-hidden">
            <div
              className="h-full bg-terracotta rounded-full transition-all duration-300 ease-out"
              style={{ width: `${uploadProgress}%` }}
            />
          </div>
        </div>
      )}

      {/* ── Validation / API error ───────────────────────────────── */}
      {displayError && (
        <div
          role="alert"
          className="flex items-start gap-3 rounded-xl bg-terracotta/8 border border-terracotta/20 px-4 py-3"
        >
          <AlertCircle className="h-4 w-4 text-terracotta shrink-0 mt-0.5" aria-hidden="true" />
          <p className="text-sm text-terracotta font-medium">{displayError}</p>
        </div>
      )}

      {/* ── Process button ───────────────────────────────────────── */}
      <button
        type="button"
        onClick={handleProcess}
        disabled={!canProcess}
        className={clsx(
          "btn-primary w-full justify-center py-3.5 text-base",
          isProcessed && "bg-sage hover:bg-sage border-none shadow-none"
        )}
        aria-busy={isLoading}
        aria-disabled={!canProcess}
      >
        {isLoading ? (
          <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />
        ) : isProcessed ? (
          <CheckCircle2 className="h-4 w-4" aria-hidden="true" />
        ) : (
          <UploadCloud className="h-4 w-4" aria-hidden="true" />
        )}
        {buttonLabel()}
      </button>

      {/* ── Helper note ─────────────────────────────────────────── */}
      {!isProcessed && (
        <p className="text-xs text-center text-text-secondary/70">
          Your file is processed and stored locally — never shared externally.
        </p>
      )}
    </div>
  );
}
