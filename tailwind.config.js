/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        "exam-blue": "#1e40af",
        "exam-green": "#10b981",
        "exam-red": "#ef4444",
        "exam-yellow": "#f59e0b",
        "exam-gray": "#6b7280"
      },
      fontFamily: {
        "sans": ["Inter", "system-ui", "-apple-system", "sans-serif"]
      }
    },
  },
  plugins: [],
}
