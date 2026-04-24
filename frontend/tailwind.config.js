/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{vue,js}'],
  theme: {
    extend: {
      colors: {
        office: {
          floor: '#f0ede8',
          wall: '#8b7d6b',
          desk: '#c4a882',
          meeting: '#7b9cc4',
          break: '#7bc47b',
          corridor: '#e0d8cc',
        },
      },
      animation: {
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
      },
    },
  },
  plugins: [],
}
