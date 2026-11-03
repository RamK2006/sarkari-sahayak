import type { Config } from 'tailwindcss';

const config: Config = {
  content: ['./src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        page: 'var(--page)',
        surface: 'var(--surface)',
        ink: { DEFAULT: 'var(--ink)', muted: 'var(--ink-muted)', faint: 'var(--ink-faint)' },
        line: { DEFAULT: 'var(--line)', strong: 'var(--line-strong)' },
        brand: { DEFAULT: 'var(--brand)', hover: 'var(--brand-hover)', soft: 'var(--brand-soft)' },
        ok: { DEFAULT: 'var(--ok)', soft: 'var(--ok-soft)' },
        warn: { DEFAULT: 'var(--warn)', soft: 'var(--warn-soft)' },
        bad: { DEFAULT: 'var(--bad)', soft: 'var(--bad-soft)' },
      },
      fontFamily: {
        sans: [
          'var(--font-inter)',
          '"Noto Sans"',
          '"Nirmala UI"',
          '"Segoe UI"',
          'system-ui',
          '-apple-system',
          'sans-serif',
        ],
      },
      fontSize: {
        sm: ['0.9375rem', { lineHeight: '1.55' }],
        base: ['1.0625rem', { lineHeight: '1.65' }],
        lg: ['1.1875rem', { lineHeight: '1.6' }],
        xl: ['1.375rem', { lineHeight: '1.4' }],
        '2xl': ['1.75rem', { lineHeight: '1.3' }],
        '3xl': ['2.25rem', { lineHeight: '1.2' }],
      },
      borderRadius: { DEFAULT: '6px', lg: '10px' },
      minHeight: { tap: '48px' },
      minWidth: { tap: '48px' },
    },
  },
  plugins: [],
};

export default config;
