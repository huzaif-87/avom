/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // TalentRank AI Editorial Contemporary Palette
        sage: {
          light: '#DCE3D8',
          muted: '#DCE3D8',
          DEFAULT: '#A8B5A2',
          dark: '#8E9D87',
          hover: '#98A692',
        },
        olive: {
          light: '#E6E9E0',
          muted: '#C4CCBE',
          DEFAULT: '#5E6B55',
          dark: '#4C5744',
          darker: '#3E4738',
          hover: '#6A7860',
        },
        cream: {
          50: '#FAF8F5',
          100: '#F2EFEA',
          200: '#E9E4DC',
          DEFAULT: '#F2EFEA',
        },
        charcoal: {
          light: '#4B524A',
          muted: '#777C73',
          DEFAULT: '#2E332D',
          dark: '#1F231E',
        },
        terracotta: {
          light: '#F8EFEA',
          DEFAULT: '#C58C78',
          dark: '#A86F5C',
          muted: '#EAD9D2',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
      },
      boxShadow: {
        '2xs': '0 1px 2px 0 rgba(46, 51, 45, 0.03)',
        'xs': '0 1px 3px 0 rgba(46, 51, 45, 0.05), 0 1px 2px -1px rgba(46, 51, 45, 0.04)',
        'sm': '0 2px 4px 0 rgba(46, 51, 45, 0.05), 0 1px 2px -1px rgba(46, 51, 45, 0.04)',
        'md': '0 4px 6px -1px rgba(46, 51, 45, 0.07), 0 2px 4px -2px rgba(46, 51, 45, 0.05)',
        'lg': '0 10px 15px -3px rgba(46, 51, 45, 0.08), 0 4px 6px -4px rgba(46, 51, 45, 0.04)',
      },
      borderRadius: {
        'xl': '0.75rem',  // 12px
        '2xl': '1rem',    // 16px
      },
    },
  },
  plugins: [],
}
