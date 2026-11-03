'use client';

import { usePathname } from 'next/navigation';
import { useI18n } from '@/lib/i18n';

export function Footer() {
  const { t } = useI18n();
  const pathname = usePathname();
  // The conversation fills the viewport; the disclaimer is shown on the other pages.
  if (pathname === '/assistant') return null;
  return (
    <footer className="border-t border-line bg-surface">
      <p className="mx-auto max-w-6xl px-4 py-5 text-sm text-ink-muted sm:px-6">{t('footer.disclaimer')}</p>
    </footer>
  );
}
