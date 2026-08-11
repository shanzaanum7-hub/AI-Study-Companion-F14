"use client";

import { useState } from "react";
import { BookOpen, Menu, X } from "lucide-react";
import clsx from "clsx";

interface NavbarProps {
  activeSection?: "workspace" | "how-it-works";
  onNavigate?: (section: "workspace" | "how-it-works") => void;
}

export default function Navbar({ activeSection = "workspace", onNavigate }: NavbarProps) {
  const [menuOpen, setMenuOpen] = useState(false);

  const navItems: { id: "workspace" | "how-it-works"; label: string }[] = [
    { id: "workspace", label: "Workspace" },
    { id: "how-it-works", label: "How It Works" },
  ];

  return (
    <header className="sticky top-0 z-50 bg-dark-brown shadow-md" role="banner">
      <div className="container-main flex h-16 items-center justify-between">

        {/* ── Logo ── */}
        <a
          href="#"
          onClick={() => onNavigate?.("workspace")}
          className="flex items-center gap-2.5 group focus-visible:outline-none"
          aria-label="AI Study Companion — go to workspace"
        >
          <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-terracotta/20 transition-colors group-hover:bg-terracotta/30">
            <BookOpen className="h-4.5 w-4.5 text-terracotta" aria-hidden="true" />
          </span>
          <span className="font-serif text-base font-semibold tracking-tight text-off-white leading-tight">
            AI Study<br />
            <span className="text-xs font-sans font-normal text-beige tracking-widest uppercase leading-none">
              Companion
            </span>
          </span>
        </a>

        {/* ── Desktop nav ── */}
        <nav className="hidden md:flex items-center gap-1" aria-label="Main navigation">
          {navItems.map((item) => (
            <button
              key={item.id}
              onClick={() => onNavigate?.(item.id)}
              className={clsx(
                "relative px-4 py-2 text-sm font-medium transition-colors rounded-lg",
                "focus-visible:outline focus-visible:outline-2 focus-visible:outline-terracotta focus-visible:outline-offset-2",
                activeSection === item.id
                  ? "text-off-white"
                  : "text-beige hover:text-off-white"
              )}
              aria-current={activeSection === item.id ? "page" : undefined}
            >
              {item.label}
              {/* Terracotta underline indicator */}
              {activeSection === item.id && (
                <span
                  className="absolute bottom-0.5 left-4 right-4 h-0.5 rounded-full bg-terracotta"
                  aria-hidden="true"
                />
              )}
            </button>
          ))}
        </nav>

        {/* ── Mobile menu button ── */}
        <button
          className="md:hidden flex h-9 w-9 items-center justify-center rounded-lg text-beige
                     hover:bg-white/10 transition-colors
                     focus-visible:outline focus-visible:outline-2 focus-visible:outline-terracotta"
          onClick={() => setMenuOpen((v) => !v)}
          aria-expanded={menuOpen}
          aria-controls="mobile-menu"
          aria-label={menuOpen ? "Close menu" : "Open menu"}
        >
          {menuOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
        </button>
      </div>

      {/* ── Mobile dropdown ── */}
      {menuOpen && (
        <nav
          id="mobile-menu"
          className="md:hidden border-t border-white/10 bg-dark-brown px-4 pb-4 pt-2"
          aria-label="Mobile navigation"
        >
          {navItems.map((item) => (
            <button
              key={item.id}
              onClick={() => { onNavigate?.(item.id); setMenuOpen(false); }}
              className={clsx(
                "flex w-full items-center gap-2 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors",
                activeSection === item.id
                  ? "bg-white/10 text-off-white"
                  : "text-beige hover:bg-white/5 hover:text-off-white"
              )}
              aria-current={activeSection === item.id ? "page" : undefined}
            >
              {activeSection === item.id && (
                <span className="h-1.5 w-1.5 rounded-full bg-terracotta" aria-hidden="true" />
              )}
              {item.label}
            </button>
          ))}
        </nav>
      )}
    </header>
  );
}
