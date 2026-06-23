/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        brand: {
          DEFAULT: "#006C32",
          dark: "#004F24",
          tint: "#E6F2EB",
        },
        ink: "#0F1A14",
        muted: "#5A6B61",
        hairline: "#E3E8E4",
        status: {
          amber: "#B45309",
          red: "#B42318",
          green: "#006C32",
        },
      },
      fontFamily: {
        sans: [
          "Inter",
          "-apple-system",
          "BlinkMacSystemFont",
          "Segoe UI",
          "Roboto",
          "Helvetica Neue",
          "Arial",
          "sans-serif",
        ],
        display: [
          "\"Source Serif 4\"",
          "\"Source Serif Pro\"",
          "Georgia",
          "serif",
        ],
      },
      borderRadius: {
        card: "14px",
      },
      boxShadow: {
        card: "0 1px 2px rgba(15, 26, 20, 0.04), 0 4px 12px rgba(15, 26, 20, 0.05)",
      },
      maxWidth: {
        page: "1100px",
      },
      fontVariantNumeric: {
        "tabular-nums": "tabular-nums",
      },
      keyframes: {
        fadeUp: {
          "0%": { opacity: "0", transform: "translateY(8px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        shimmer: {
          "0%": { backgroundPosition: "-200% 0" },
          "100%": { backgroundPosition: "200% 0" },
        },
      },
      animation: {
        "fade-up": "fadeUp 400ms ease-out both",
        shimmer: "shimmer 1.6s linear infinite",
      },
    },
  },
  plugins: [],
};
