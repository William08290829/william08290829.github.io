/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: "selector",
  content: ["./src/templates/**/*.html"],
  theme: {
    extend: {
      fontFamily: {
        sans: ["IBM Plex Sans", "sans-serif"],
        mono: ["IBM Plex Mono", "monospace"],
        serif: ["Crimson Pro", "Georgia", "serif"],
      },
    },
  },
  plugins: [require("@tailwindcss/typography")],
};
