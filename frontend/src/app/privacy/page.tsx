'use client';

import { useState } from 'react';
import { Trash2 } from 'lucide-react';
import { useI18n } from '@/lib/i18n';

export default function PrivacyPage() {
  const { t } = useI18n();
  const [confirming, setConfirming] = useState(false);
  const [cleared, setCleared] = useState(false);

  const clearAll = () => {
    try {
      Object.keys(localStorage)
        .filter((k) => k.startsWith('sa.') && k !== 'sa.language' && k !== 'sa.theme')
        .forEach((k) => localStorage.removeItem(k));
    } catch {
      /* storage unavailable */
    }
    setConfirming(false);
    setCleared(true);
    // Reload so every part of the app drops what it held in memory.
    setTimeout(() => window.location.reload(), 1200);
  };

  return (
    <main id="main" className="mx-auto w-full max-w-3xl px-4 py-8 sm:px-6 sm:py-12">
      <h1 className="text-3xl">{t('privacy.title')}</h1>
      <p className="mt-2 text-ink-muted">{t('privacy.subtitle')}</p>

      <div className="mt-8 divide-y divide-line border-y border-line">
        {[1, 2, 3].map((n) => (
          <section key={n} className="py-5">
            <h2 className="text-xl">{t(`privacy.s${n}_title`)}</h2>
            <p className="mt-2 text-ink-muted">{t(`privacy.s${n}_text`)}</p>
          </section>
        ))}
      </div>

      <div className="mt-8">
        {cleared ? (
          <p role="status" className="text-ok">{t('privacy.cleared')}</p>
        ) : confirming ? (
          <div role="alertdialog" aria-label={t('privacy.clear')} className="rounded-lg border border-bad/30 bg-bad-soft p-4">
            <p className="text-bad">{t('privacy.clear_confirm')}</p>
            <div className="mt-3 flex gap-3">
              <button type="button" className="btn-secondary" onClick={() => setConfirming(false)}>{t('common.cancel')}</button>
              <button type="button" className="btn border-bad bg-bad text-onbrand hover:opacity-90" onClick={clearAll}>{t('common.confirm')}</button>
            </div>
          </div>
        ) : (
          <button type="button" className="btn-secondary" onClick={() => setConfirming(true)}>
            <Trash2 aria-hidden className="h-5 w-5" />
            {t('privacy.clear')}
          </button>
        )}
      </div>
    </main>
  );
}
