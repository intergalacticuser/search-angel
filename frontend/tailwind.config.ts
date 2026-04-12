import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx}",
    "./components/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        angel: {
          bg: "#0a0a0f",
          surface: "#12121a",
          border: "#1e1e2e",
          text: "#e2e2e8",
          muted: "#8888a0",
          accent: "#00d4ff",
          "accent-dim": "#00a3c4",
          green: "#22c55e",
          amber: "#eab308",
          red: "#ef4444",
        },
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
        mono: ["JetBrains Mono", "Fira Code", "monospace"],
      },
    },
  },
  plugins: [],
};

export default config;
