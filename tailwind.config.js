/** Tailwind CSS v3 (standalone CLI, Node.js kerak emas). */
module.exports = {
  content: ["./templates/**/*.html", "./naryad/**/*.py", "./static/js/app.js"],
  // Tungi rejim: <html class="dark"> (static/js/theme.js sahifa chizilishidan oldin qo'yadi)
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        // Asosiy rang — to'q ko'k (12-bosqich qarori; CLAUDE.md 10-bo'lim, 58-band)
        brand: {
          50: "#eef3fb",
          100: "#d9e3f5",
          200: "#b6c8ea",
          300: "#89a5d9",
          400: "#5a7ec4",
          500: "#3a5fae",
          600: "#2a4a93",
          700: "#213b78",
          800: "#1b3060",
          900: "#142548",
          950: "#0b1730",
        },
        // Aksent — emblemadagi oltin (kaduchey)
        gold: {
          50: "#fdf8ec",
          100: "#f9edc9",
          200: "#f2d98d",
          300: "#e9c255",
          400: "#d9a83a",
          500: "#c08f26",
          600: "#9c711d",
          700: "#7a571a",
          800: "#5f4419",
          900: "#4a3616",
        },
      },
    },
  },
  plugins: [],
};
