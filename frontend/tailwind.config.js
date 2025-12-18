/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        // Dark theme inspired by Ableton Live
        'ableton': {
          'bg': '#1e1e1e',
          'surface': '#2d2d2d',
          'surface-light': '#3d3d3d',
          'border': '#4a4a4a',
          'text': '#e8e8e8',
          'text-muted': '#a0a0a0',
          'accent': '#ff764d',
          'accent-hover': '#ff8f6d',
          'success': '#5cb85c',
          'warning': '#f0ad4e',
          'danger': '#d9534f',
          'purple': '#9b59b6',
          'blue': '#3498db',
        }
      },
      fontFamily: {
        'mono': ['JetBrains Mono', 'Fira Code', 'monospace'],
        'sans': ['Instrument Sans', 'system-ui', 'sans-serif'],
      },
      animation: {
        'waveform': 'waveform 1s ease-in-out infinite',
        'pulse-subtle': 'pulse-subtle 2s ease-in-out infinite',
        'slide-up': 'slide-up 0.3s ease-out',
        'fade-in': 'fade-in 0.2s ease-out',
      },
      keyframes: {
        'waveform': {
          '0%, 100%': { transform: 'scaleY(0.5)' },
          '50%': { transform: 'scaleY(1)' },
        },
        'pulse-subtle': {
          '0%, 100%': { opacity: '1' },
          '50%': { opacity: '0.7' },
        },
        'slide-up': {
          '0%': { transform: 'translateY(10px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
        'fade-in': {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
      },
    },
  },
  plugins: [],
}

