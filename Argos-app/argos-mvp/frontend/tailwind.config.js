/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        display: ['Inter', 'system-ui', 'sans-serif'],
      },
      colors: {
        // INFYN verde — #2ED47A acento (Argos primary), #0F7B53 principal (botones/acciones)
        argos: {
          50:  '#F0FDF7',
          100: '#C8F5E0',
          200: '#8EEDC4',
          300: '#4DD9A0',
          400: '#2ED47A', // INFYN verde acento — highlight principal de Argos
          500: '#22B864',
          600: '#0F7B53', // INFYN verde principal — botones, activos
          700: '#0A5C3E',
          800: '#0A3F2C', // INFYN verde oscuro
          900: '#061F16',
        },
        // Surface dark-first — 50 = base oscura, 900 = texto claro
        surface: {
          50:  '#060D09', // INFYN fondo oscuro — background principal
          100: '#0C1812', // card / panel background
          200: '#162818', // bordes sutiles
          300: '#1E3824',
          400: '#527A62', // texto muted / desactivado
          500: '#7A9A88', // texto secundario
          600: '#9ABAA8',
          700: '#C0D4C8',
          800: '#DDE8E2',
          900: '#F5F7F6', // INFYN gris claro — texto principal
        },
        accent: {
          orange: '#f97316',
          amber: '#f59e0b',
          red: '#ef4444',
          blue: '#3b82f6',
        },
      },
    },
  },
  plugins: [],
}
