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
    },
  },
  plugins: [],
};

export default config;
