/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        ink: {
          950: '#070a14',
          900: '#0b1020',
          850: '#0f1528',
          800: '#141b33',
          700: '#1c2542',
          600: '#27325a',
        },
        brand: {
          50: '#eef4ff',
          100: '#d9e6ff',
          200: '#bcd3ff',
          300: '#8eb5ff',
          400: '#5a8cff',
          500: '#3366ff',
          600: '#1f4ae0',
          700: '#1a3bb8',
          800: '#1a3390',
          900: '#1b2f72',
        },
        accent: {
          400: '#7c5cff',
          500: '#6a3cff',
          600: '#5a2ae6',
        },
        ok: { 400: '#34d399', 500: '#10b981' },
        warn: { 400: '#fbbf24', 500: '#f59e0b' },
        bad: { 400: '#f87171', 500: '#ef4444' },
      },
      fontFamily: {
        sans: ['Inter', 'ui-sans-serif', 'system-ui', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'ui-monospace', 'monospace'],
      },
      boxShadow: {
        glow: '0 0 0 1px rgba(90,140,255,0.18), 0 18px 60px -20px rgba(90,140,255,0.45)',
        'glow-accent': '0 0 0 1px rgba(124,92,255,0.22), 0 18px 60px -20px rgba(124,92,255,0.5)',
        card: '0 10px 40px -12px rgba(0,0,0,0.6)',
      },
      backgroundImage: {
        'grid-faint':
          'linear-gradient(rgba(255,255,255,0.03) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.03) 1px, transparent 1px)',
        'ai-radial':
          'radial-gradient(900px 500px at 15% -10%, rgba(51,102,255,0.18), transparent 60%), radial-gradient(700px 500px at 100% 0%, rgba(124,92,255,0.16), transparent 55%)',
      },
      keyframes: {
        'fade-up': {
          '0%': { opacity: '0', transform: 'translateY(8px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        shimmer: {
          '0%': { backgroundPosition: '-200% 0' },
          '100%': { backgroundPosition: '200% 0' },
        },
        'pulse-soft': {
          '0%,100%': { opacity: '1' },
          '50%': { opacity: '0.55' },
        },
        'spin-slow': {
          '0%': { transform: 'rotate(0deg)' },
          '100%': { transform: 'rotate(360deg)' },
        },
      },
      animation: {
        'fade-up': 'fade-up 0.5s ease-out both',
        shimmer: 'shimmer 2.2s linear infinite',
        'pulse-soft': 'pulse-soft 1.6s ease-in-out infinite',
        'spin-slow': 'spin-slow 1.1s linear infinite',
      },
    },
  },
  plugins: [],
};
