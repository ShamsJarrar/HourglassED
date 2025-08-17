/** @type {import('tailwindcss').Config} */
export default {
	content: [
		'./index.html',
		'./src/**/*.{ts,tsx}',
	],
	theme: {
		extend: {
			colors: {
				brand: {
					DEFAULT: '#633D00',
				},
				stroke: '#DCDCDC',
				bg: '#FFF8EB',
				text: '#FAF0DC',
			},
			fontFamily: {
				sans: ['Instrument Sans', 'ui-sans-serif', 'system-ui'],
			},
		},
	},
	plugins: [],
}


