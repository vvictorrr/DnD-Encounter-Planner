/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      fontFamily: {
        display: ["Fraunces", "serif"],
        mono2: ["IBM Plex Mono", "monospace"],
      },
    },
  },
  plugins: [],
};
