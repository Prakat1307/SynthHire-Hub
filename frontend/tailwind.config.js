
module.exports = {
    darkMode: 'class',
    content: [
        './pages*.{js,ts,jsx,tsx,mdx}',
        './components*.{js,ts,jsx,tsx,mdx}',
        './app*.{js,ts,jsx,tsx,mdx}',
    ],
    theme: {
        extend: {
            colors: {
                cyber: {
                    slate: {
                        950: '#09090b', 
                        900: '#18181b', 
                        800: '#27272a', 
                        700: '#3f3f46', 
                    },
                    teal: {
                        500: '#3b82f6', 
                        400: '#60a5fa', 
                        900: '#1e3a8a', 
                    },
                    purple: {
                        500: '#8b5cf6', 
                        400: '#a78bfa', 
                        900: '#4c1d95', 
                    },
                    violet: {
                        500: '#8b5cf6',
                    },
                },
                glass: {
                    100: 'rgba(255, 255, 255, 0.05)',
                    200: 'rgba(255, 255, 255, 0.1)',
                    border: 'rgba(255, 255, 255, 0.1)',
                },
            },
            animation: {
                'pulse-slow': 'pulse 4s cubic-bezier(0.4, 0, 0.6, 1) infinite',
                'float': 'float 6s ease-in-out infinite',
                'glow': 'glow 2s ease-in-out infinite alternate',
                'shimmer': 'shimmer 2s linear infinite',
            },
            keyframes: {
                float: {
                    '0%, 100%': { transform: 'translateY(0)' },
                    '50%': { transform: 'translateY(-10px)' },
                },
                glow: {
                    '0%': { boxShadow: '0 0 5px rgba(20, 184, 166, 0.5)' },
                    '100%': { boxShadow: '0 0 20px rgba(20, 184, 166, 0.8), 0 0 10px rgba(168, 85, 247, 0.5)' },
                },
                shimmer: {
                    'from': { backgroundPosition: '0 0' },
                    'to': { backgroundPosition: '-200% 0' },
                },
            },
            backgroundImage: {
                'gradient-radial': 'radial-gradient(var(--tw-gradient-stops))',
                'hero-pattern': "url('/grid.svg')",
            },
        },
    },
    plugins: [],
}
