import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
    "./lib/**/*.{ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // ── Core palette ──────────────────────────────────────────
        background:  "#F5EFE4",
        "dark-brown": "#40352F",
        terracotta:  "#B9684E",
        "terracotta-hover": "#A05840",
        sage:        "#87977B",
        "sage-light": "#C4CEBC",
        beige:       "#D8C7B1",
        "off-white":  "#FBF8F2",
        // ── Semantic aliases ──────────────────────────────────────
        card:        "#FBF8F2",
        border:      "#D8C7B1",
        "text-primary":   "#40352F",
        "text-secondary": "#7A6A5E",
        success:     "#87977B",
        "ai-bg":     "#EFF2EB",  // very light sage for AI sections
      },
      fontFamily: {
        sans: ["var(--font-geist-sans)", "ui-sans-serif", "system-ui", "sans-serif"],
        serif: ["var(--font-playfair)", "Georgia", "serif"],
        mono: ["var(--font-geist-mono)", "ui-monospace", "monospace"],
      },
      borderRadius: {
        "2xl": "1rem",
        "3xl": "1.5rem",
      },
      boxShadow: {
        card:   "0 2px 16px 0 rgba(64,53,47,0.07)",
        "card-hover": "0 6px 28px 0 rgba(64,53,47,0.13)",
        terracotta: "0 4px 18px 0 rgba(185,104,78,0.22)",
      },
      animation: {
        "float":        "float 4s ease-in-out infinite",
        "fade-in":      "fadeIn 0.5s ease forwards",
        "slide-up":     "slideUp 0.5s ease forwards",
        "spin-slow":    "spin 8s linear infinite",
        "pulse-slow":   "pulse 3s ease-in-out infinite",
        "bounce-slow":  "bounce 2.5s ease-in-out infinite",
        "dash":         "dash 2s ease-in-out infinite",
      },
      keyframes: {
        float: {
          "0%, 100%": { transform: "translateY(0px)" },
          "50%":      { transform: "translateY(-8px)" },
        },
        fadeIn: {
          from: { opacity: "0" },
          to:   { opacity: "1" },
        },
        slideUp: {
          from: { opacity: "0", transform: "translateY(20px)" },
          to:   { opacity: "1", transform: "translateY(0)" },
        },
        dash: {
          "0%":   { strokeDashoffset: "200" },
          "100%": { strokeDashoffset: "0" },
        },
      },
      backgroundImage: {
        "dot-pattern": "radial-gradient(circle, #D8C7B1 1px, transparent 1px)",
      },
      backgroundSize: {
        "dot-sm": "20px 20px",
      },
    },
  },
  plugins: [],
};

export default config;
