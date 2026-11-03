'use client';

import Link from 'next/link';
import { useI18n } from '@/lib/i18n';

export default function NotFound() {
  const { t } = useI18n();
  return (
    <main id="main" className="mx-auto w-full max-w-3xl px-4 py-16 sm:px-6">
      <h1 className="text-2xl">{t('notfound.title')}</h1>
      <p className="mt-2 text-ink-muted">{t('notfound.text')}</p>
      <Link href="/" className="btn-primary mt-6">{t('nav.home')}</Link>
    </main>
  );
}
