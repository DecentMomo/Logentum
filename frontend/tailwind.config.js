/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        slateNight: '#0b1220',
        steel: '#0f172a',
        accent: '#2dd4bf',
        glow: '#22d3ee'
      },
      boxShadow: {
        panel: '0 10px 30px rgba(2, 6, 23, 0.45)'
      },
      fontFamily: {
        heading: ['Sora', 'sans-serif'],
        body: ['Manrope', 'sans-serif'],
        mono: ['IBM Plex Mono', 'monospace']
      },
      backgroundImage: {
        grid: 'linear-gradient(rgba(148,163,184,0.07) 1px, transparent 1px), linear-gradient(90deg, rgba(148,163,184,0.07) 1px, transparent 1px)'
      },
      animation: {
        'fade-in': 'fadeIn 500ms ease-out',
        'rise-up': 'riseUp 450ms ease-out'
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' }
        },
        riseUp: {
          '0%': { opacity: '0', transform: 'translateY(10px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' }
        }
      }
    }
  },
  plugins: []
};
