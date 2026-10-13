/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        primary: 'var(--primary)',
        accent: 'var(--accent)',
        danger: 'var(--danger)',
        success: 'var(--success)',
        bg: 'var(--bg)',
        surface: 'var(--surface)',
        'text-main': 'var(--text)',
        'text-muted': 'var(--text-muted)',
      },
      borderRadius: {
        'xl': 'var(--radius)',
        '2xl': 'var(--radius-lg)',
      },
      boxShadow: {
        'card': 'var(--shadow)',
        'card-hover': 'var(--shadow-hover)',
      },
      transitionTimingFunction: {
        'lusion': 'cubic-bezier(.35, 0, 0, 1)',
        'lusion-out': 'cubic-bezier(.16, 1, .3, 1)',
      },
      fontFamily: {
        sans: ['system-ui', 'Segoe UI', 'Roboto', 'Helvetica', 'Arial', 'sans-serif'],
        mono: ['ui-monospace', 'SFMono-Regular', 'Consolas', 'Liberation Mono', 'Menlo', 'monospace'],
      },
    },
  },
  plugins: [],
}
