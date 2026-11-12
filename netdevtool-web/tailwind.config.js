/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        brand: {
          DEFAULT: '#3268DB',
          soft: '#EAF1FF',
          strong: '#2D5EBD',
          line: '#C6D7FF',
        },
        ink: {
          900: '#202C40',
          700: '#33415C',
          500: '#647289',
          400: '#8A96A8',
          300: '#A9B3C2',
        },
        line: '#E4EAF2',
        'line-soft': '#EDF1F7',
        'input-border': '#C9D6ED',
        page: '#F7F9FC',
        nav: '#F1F4F9',
        panel: '#FFFFFF',
        soft: '#F8FAFD',
        head: '#FAFCFF',
        success: {
          DEFAULT: '#29826D',
          soft: '#EDF7F3',
          line: '#C8E6DC',
        },
        warn: {
          DEFAULT: '#B47B24',
          soft: '#FFF7E8',
          line: '#F0DDBB',
        },
        danger: {
          DEFAULT: '#C45C60',
          soft: '#FDF1F1',
          line: '#F0D2D4',
        },
        'code-blue': '#2D5EBD',
      },
      fontFamily: {
        sans: [
          '"Noto Sans SC"',
          '"PingFang SC"',
          '"Microsoft YaHei"',
          'system-ui',
          'sans-serif',
        ],
        mono: ['"IBM Plex Mono"', '"JetBrains Mono"', 'Consolas', 'monospace'],
      },
      boxShadow: {
        panel: '0 1px 2px 0 rgba(32, 44, 64, 0.03)',
        input: '0px 4px 20px 0px rgba(35, 60, 104, 0.06)',
      },
      borderRadius: {
        panel: '12px',
      },
    },
  },
  plugins: [],
}
