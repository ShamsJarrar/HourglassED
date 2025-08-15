/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        // HourglassED Custom Colors
        'hourglass': {
          'yellow': '#ffd21f',
          'yellow-light': '#ffe066',
          'yellow-dark': '#e6bd00',
          'brown': '#633d00',
          'brown-light': '#8b5400',
          'brown-lighter': '#b36f00',
          'cream': '#faf0dc',
          'cream-dark': '#f5e6c8',
          'cream-light': '#fff8eb',
        }
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
      borderRadius: {
        'xl': '20px',
        'lg': '16px',
        'md': '12px',
        'sm': '8px',
      }
    },
  },
  plugins: [],
}
