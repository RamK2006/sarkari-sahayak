'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { Globe } from 'lucide-react';
import { useI18n } from '@/lib/i18n';
import { LANGUAGES } from '@/lib/languages';

export function Header() {
  const { t, language, setLanguage } = useI18n();
  const pathname = usePathname();

  const links = [
    { href: '/assistant', label: t('nav.assistant') },
    { href: '/schemes', label: t('nav.schemes') },
  ];

  return (
    <header className="border-b border-line bg-surface">
      <a
        href="#main"
        className="sr-only focus:not-sr-only focus:absolute focus:left-2 focus:top-2 focus:z-50 focus:rounded focus:bg-brand focus:px-4 focus:py-2 focus:text-white"
      >
        {t('app.skip_to_content')}
      </a>
      <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-x-6 gap-y-2 px-4 py-2 sm:px-6">
        <Link href="/" className="min-h-tap py-3 text-lg font-semibold text-ink">
          {t('app.name')}
        </Link>

        <div className="flex items-center gap-1 sm:gap-3">
          <nav aria-label={t('nav.menu')} className="flex items-center">
            {links.map((l) => {
              const active = pathname === l.href || pathname.startsWith(`${l.href}/`);
              return (
                <Link
                  key={l.href}
                  href={l.href}
                  aria-current={active ? 'page' : undefined}
                  className={`flex min-h-tap items-center border-b-2 px-3 font-medium ${
                    active ? 'border-brand text-brand' : 'border-transparent text-ink-muted hover:text-ink'
                  }`}
                >
                  {l.label}
                </Link>
              );
            })}
          </nav>

          <label className="relative flex items-center">
            <span className="sr-only">{t('nav.language')}</span>
            <Globe aria-hidden className="pointer-events-none absolute left-3 h-4 w-4 text-ink-muted" />
            <select
              value={language}
              onChange={(e) => setLanguage(e.target.value)}
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
      </div>
    </header>
  );
}
