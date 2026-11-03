'use client';

import { useI18n } from '@/lib/i18n';

const COUNT = 6;

export default function HelpPage() {
  const { t } = useI18n();
  return (
    <main id="main" className="mx-auto w-full max-w-3xl px-4 py-8 sm:px-6 sm:py-12">
      <h1 className="text-3xl">{t('help.title')}</h1>
      <p className="mt-2 text-ink-muted">{t('help.subtitle')}</p>
      <div className="mt-8 divide-y divide-line border-y border-line">
        {Array.from({ length: COUNT }, (_, i) => i + 1).map((n) => (
          <details key={n} className="group py-1">
            <summary className="flex min-h-tap cursor-pointer list-none items-center justify-between gap-4 py-3 font-display text-lg font-semibold">
              {t(`help.q${n}`)}
              <span aria-hidden className="text-2xl text-brand transition-transform group-open:rotate-45">+</span>
            </summary>
            <p className="pb-4 text-ink-muted">{t(`help.a${n}`)}</p>
          </details>
        ))}
      </div>
    </main>
  );
}
