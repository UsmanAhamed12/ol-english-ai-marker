/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        paper: "#f7f4ec",
        paperDeep: "#efe9da",
        ink: "#17170f",
        inkSoft: "#6b6759",
        red: "#9e3b26",
        redWash: "#f6e2da",
        sage: "#4a6b57",
        sageWash: "#e4ede5",
        gold: "#f2dd9a",
        line: "#ddd6c4",
      },
      fontFamily: {
        display: ["Fraunces", "Georgia", "Times New Roman", "serif"],
        body: ["Inter", "ui-sans-serif", "system-ui", "sans-serif"],
      },
    },
  },
  plugins: [],
};