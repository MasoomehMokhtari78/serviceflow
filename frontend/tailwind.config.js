/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        vazir: ['Vazirmatn', 'system-ui', 'sans-serif'],
      },
      colors: {
        brand: {
          50: '#fdf8f6',
          100: '#f2e8e5',
          200: '#eaddd7',
          500: '#8b5e3c',
          600: '#6f4526',
          700: '#533118',
          800: '#3a200e',
          900: '#261408',
        },
        kds: {
          pending: '#f59e0b',
          preparing: '#3b82f6',
          ready: '#10b981',
          delayed: '#ef4444',
          served: '#6b7280'
        }
      }
    },
  },
  plugins: [],
}
