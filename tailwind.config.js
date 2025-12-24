/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./app/templates/**/*.html",
    "./app/static/js/**/*.js",
  ],
  theme: {
    extend: {
      fontFamily: {
        display: ['"Space Grotesk"', '"Manrope"', 'system-ui', 'sans-serif'],
        body: ['"Inter"', 'system-ui', 'sans-serif'],
      },
      colors: {
        primary: {
          DEFAULT: "#0F172A",
          light: "#1E293B",
          accent: "#06B6D4",
        },
        accent: "#F59E0B",
      },
      boxShadow: {
        soft: "0 10px 40px -10px rgba(15, 23, 42, 0.2)",
      },
    },
  },
  plugins: [require("@tailwindcss/typography"), require("@tailwindcss/forms")],
};
