'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { Globe, Moon, Sun } from 'lucide-react';
import { useEffect, useState } from 'react';
import { useI18n } from '@/lib/i18n';
import { LANGUAGES } from '@/lib/languages';

function ThemeToggle() {
  const { t } = useI18n();
  const [theme, setTheme] = useState<'light' | 'dark'>('light');

  useEffect(() => setTheme(document.documentElement.dataset.theme === 'dark' ? 'dark' : 'light'), []);

  const toggle = () => {
    const next = theme === 'dark' ? 'light' : 'dark';
    document.documentElement.dataset.theme = next;
    setTheme(next);
    try {
      localStorage.setItem('sa.theme', next);
    } catch {
      /* storage unavailable */
    }
  };
  const label = t(theme === 'dark' ? 'theme.to_light' : 'theme.to_dark');
  return (
    <button type="button" onClick={toggle} aria-label={label} title={label} className="btn-quiet min-w-tap px-0">
      {theme === 'dark' ? <Sun aria-hidden className="h-5 w-5" /> : <Moon aria-hidden className="h-5 w-5" />}
    </button>
  );
}

export function Header() {
  const { t, language, setLanguage, preparing } = useI18n();
  const pathname = usePathname();

  const links = [
    { href: '/talk', label: t('nav.talk') },
    { href: '/khoj', label: t('nav.khoj') },
    { href: '/check', label: t('nav.check') },
    { href: '/vault', label: t('nav.vault') },
  ];

  return (
    <header className="border-b border-line bg-surface">
      <a
        href="#main"
        className="sr-only focus:not-sr-only focus:absolute focus:left-2 focus:top-2 focus:z-50 focus:rounded focus:bg-brand focus:px-4 focus:py-2 focus:text-onbrand"
      >
        {t('app.skip_to_content')}
      </a>
      <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-x-6 gap-y-1 px-4 py-1 sm:px-6">
        <Link href="/" className="min-h-tap py-3 font-display text-xl font-semibold text-ink">
          {t('app.name')}
        </Link>

        <div className="flex items-center gap-1">
          <ThemeToggle />
          <label className="relative flex items-center">
            <span className="sr-only">{t('nav.language')}</span>
            <Globe aria-hidden className="pointer-events-none absolute left-3 h-4 w-4 text-ink-muted" />
            <select
              value={language}
              onChange={(e) => setLanguage(e.target.value)}
              aria-busy={preparing}
              className="min-h-tap cursor-pointer appearance-none rounded border border-line-strong bg-surface py-2 pl-9 pr-3 font-medium text-ink"
            >
              {LANGUAGES.map((l) => (
                <option key={l.code} value={l.code} lang={l.code}>
                  {l.name}
                </option>
              ))}
            </select>
          </label>
        </div>

        <nav aria-label={t('nav.menu')} className="-mx-1 flex w-full items-center overflow-x-auto">
          {links.map((l) => {
            const active = pathname === l.href || pathname.startsWith(`${l.href}/`);
            return (
              <Link
                key={l.href}
                href={l.href}
                aria-current={active ? 'page' : undefined}
                className={`flex min-h-tap shrink-0 items-center border-b-2 px-3 font-medium ${
                  active ? 'border-brand text-brand' : 'border-transparent text-ink-muted hover:text-ink'
                }`}
              >
                {l.label}
              </Link>
            );
          })}
        </nav>
      </div>
    </header>
  );
}
