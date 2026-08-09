import { BookOpen, Sparkles } from "lucide-react";

export default function Footer() {
  return (
    <footer className="bg-dark-brown text-beige" role="contentinfo">
      <div className="container-main py-10">
        <div className="flex flex-col items-center gap-4 sm:flex-row sm:justify-between">

          {/* Brand */}
          <div className="flex items-center gap-2.5">
            <span className="flex h-7 w-7 items-center justify-center rounded-lg bg-terracotta/20">
              <BookOpen className="h-4 w-4 text-terracotta" aria-hidden="true" />
            </span>
            <span className="font-serif text-sm font-semibold text-off-white">
              AI Study Companion
            </span>
          </div>

          {/* Week badge */}
          <div className="flex items-center gap-1.5 rounded-full bg-white/5 px-4 py-1.5 text-xs">
            <Sparkles className="h-3 w-3 text-terracotta" aria-hidden="true" />
            <span className="text-beige/80">AI &amp; GenAI Fellowship — Week 3</span>
          </div>

          {/* Tech stack */}
          <p className="text-xs text-beige/50 text-center sm:text-right">
            Next.js · FastAPI · Qdrant · Gemini
          </p>
        </div>

        <div className="mt-6 border-t border-white/10 pt-6 text-center text-xs text-beige/40">
          <p>
            Scope: Document ingestion · Chunking · Embeddings · Vector storage ·
            Retrieval · Study-plan generation
          </p>
        </div>
      </div>
    </footer>
  );
}
