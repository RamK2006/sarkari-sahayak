'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useI18n } from '@/lib/i18n';

export function Footer() {
  const { t } = useI18n();
  const pathname = usePathname();
  // The conversation and guide fill the viewport; the footer is shown on the other pages.
  if (pathname === '/talk' || pathname === '/guide') return null;
  return (
    <footer className="border-t border-line bg-surface">
      <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-x-8 gap-y-2 px-4 py-5 text-sm text-ink-muted sm:px-6">
        <p className="max-w-2xl">{t('footer.disclaimer')}</p>
        <nav className="flex gap-4" aria-label={t('footer.help')}>
          <Link href="/help" className="min-h-tap py-3 font-medium text-brand underline underline-offset-4">{t('footer.help')}</Link>
          <Link href="/privacy" className="min-h-tap py-3 font-medium text-brand underline underline-offset-4">{t('footer.privacy')}</Link>
        </nav>
      </div>
    </footer>
  );
}
