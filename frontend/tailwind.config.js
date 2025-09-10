/** @type {import('tailwindcss').Config} */
module.exports = {
    content: [
        "./src/**/*.{js,jsx,ts,tsx}",
    ],
    theme: {
        extend: {
            fontFamily: {
                'sans': ['Inter', 'system-ui', 'sans-serif'],
            },
            colors: {
                'compliance': {
                    'hipaa': '#ef4444',
                    'pci': '#f97316',
                    'sox': '#8b5cf6',
                    'fisma': '#3b82f6',
                    'ferpa': '#10b981',
                }
            },
            animation: {
                'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
            }
        },
    },
    plugins: [],
}
