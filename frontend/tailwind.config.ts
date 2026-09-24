import type { Config } from "tailwindcss";

function withVar(variable: string): string {
  return `rgb(var(${variable}) / <alpha-value>)`;
}

const config: Config = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./features/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          50: withVar("--color-primary-50"),
          100: withVar("--color-primary-100"),
          200: withVar("--color-primary-200"),
          300: withVar("--color-primary-300"),
          400: withVar("--color-primary-400"),
          500: withVar("--color-primary-500"),
          600: withVar("--color-primary-600"),
          700: withVar("--color-primary-700"),
          800: withVar("--color-primary-800"),
          900: withVar("--color-primary-900"),
        },
        bg: {
          DEFAULT: withVar("--color-bg"),
          subtle: withVar("--color-bg-subtle"),
          muted: withVar("--color-bg-muted"),
          elevated: withVar("--color-bg-elevated"),
        },
        text: {
          DEFAULT: withVar("--color-text"),
          muted: withVar("--color-text-muted"),
          subtle: withVar("--color-text-subtle"),
        },
        border: {
          DEFAULT: withVar("--color-border"),
          strong: withVar("--color-border-strong"),
        },
        success: {
          DEFAULT: withVar("--color-success"),
          bg: withVar("--color-success-bg"),
        },
        warning: {
          DEFAULT: withVar("--color-warning"),
          bg: withVar("--color-warning-bg"),
        },
        danger: {
          DEFAULT: withVar("--color-danger"),
          bg: withVar("--color-danger-bg"),
        },
      },
      fontFamily: {
        // System stack: SF Pro on Apple platforms, the platform's own UI
        // face everywhere else. No webfont, so no flash and no download.
        sans: [
          "-apple-system",
          "BlinkMacSystemFont",
          "SF Pro Text",
          "Segoe UI",
          "Roboto",
          "Helvetica Neue",
          "Arial",
          "sans-serif",
        ],
      },
      fontSize: {
        // Apple's type ramp, with line heights and tracking baked in.
        caption: ["0.75rem", { lineHeight: "1rem", letterSpacing: "0" }],
        footnote: ["0.8125rem", { lineHeight: "1.125rem", letterSpacing: "-0.006em" }],
        subhead: ["0.9375rem", { lineHeight: "1.25rem", letterSpacing: "-0.01em" }],
        body: ["1.0625rem", { lineHeight: "1.5rem", letterSpacing: "-0.011em" }],
        headline: ["1.0625rem", { lineHeight: "1.375rem", letterSpacing: "-0.011em" }],
        title3: ["1.25rem", { lineHeight: "1.5rem", letterSpacing: "-0.015em" }],
        title2: ["1.375rem", { lineHeight: "1.75rem", letterSpacing: "-0.018em" }],
        title1: ["1.75rem", { lineHeight: "2.125rem", letterSpacing: "-0.021em" }],
        largeTitle: ["2.125rem", { lineHeight: "2.5rem", letterSpacing: "-0.024em" }],
      },
      borderRadius: {
        // Continuous-corner feel: larger radii than the web default.
        lg: "0.75rem",
        xl: "1rem",
        "2xl": "1.25rem",
      },
      spacing: {
        // 8pt rhythm additions.
        18: "4.5rem",
        22: "5.5rem",
      },
      transitionTimingFunction: {
        // Apple's standard ease - quick out, gentle settle.
        apple: "cubic-bezier(0.32, 0.72, 0, 1)",
      },
      keyframes: {
        shimmer: {
          "100%": { transform: "translateX(100%)" },
        },
        "fade-in": {
          from: { opacity: "0" },
          to: { opacity: "1" },
        },
        "scale-in": {
          from: { opacity: "0", transform: "scale(0.96) translateY(4px)" },
          to: { opacity: "1", transform: "scale(1) translateY(0)" },
        },
        "slide-up": {
          from: { opacity: "0", transform: "translateY(8px)" },
          to: { opacity: "1", transform: "translateY(0)" },
        },
      },
      animation: {
        shimmer: "shimmer 1.8s infinite",
        "fade-in": "fade-in 0.2s cubic-bezier(0.32, 0.72, 0, 1)",
        "scale-in": "scale-in 0.22s cubic-bezier(0.32, 0.72, 0, 1)",
        "slide-up": "slide-up 0.24s cubic-bezier(0.32, 0.72, 0, 1)",
      },
    },
  },
  plugins: [],
};

export default config;
