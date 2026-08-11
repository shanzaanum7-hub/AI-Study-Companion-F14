import type { Metadata, Viewport } from "next";
import "./globals.css";

/* ── Metadata ────────────────────────────────────────────────────────── */

export const metadata: Metadata = {
  title: "AI Study Companion — Week 3",
  description:
    "Upload study notes, retrieve relevant content with semantic AI search, " +
    "and generate a personalised study plan powered by Gemini and Qdrant.",
  keywords: [
    "AI Study Companion",
    "RAG",
    "Qdrant",
    "Gemini embeddings",
    "study plan",
    "semantic search",
    "document retrieval",
  ],
  authors: [{ name: "AI & GenAI Fellowship" }],
  robots: { index: false, follow: false },
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  themeColor: "#40352F",
};

/* ── Root layout ─────────────────────────────────────────────────────── */

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-background antialiased">
        {children}
      </body>
    </html>
  );
}