'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { ArrowRight } from 'lucide-react';
import { api } from '@/lib/api';
import { useI18n } from '@/lib/i18n';
import { LANGUAGES } from '@/lib/languages';
import { useSession } from '@/lib/session';

export default function Home() {
  const { t, language, setLanguage } = useI18n();
  const { profile, skipped } = useSession();
  const [count, setCount] = useState<number | null>(null);

  useEffect(() => {
    api.meta().then((m) => setCount(m.scheme_count)).catch(() => setCount(null));
  }, []);

  const started = Object.keys(profile).length + skipped.length > 0;
  const steps = [1, 2, 3].map((n) => ({ title: t(`home.step${n}_title`), text: t(`home.step${n}_text`) }));

  return (
    <main id="main" className="mx-auto grid w-full max-w-6xl gap-12 px-4 py-10 sm:px-6 lg:grid-cols-[1.15fr_1fr] lg:gap-16 lg:py-16">
      <section>
        <h1 className="text-3xl sm:text-4xl">{t('home.title')}</h1>
        <p className="mt-4 max-w-xl text-lg text-ink-muted">{t('home.subtitle')}</p>

        <fieldset className="mt-8">
          <legend className="mb-3 font-medium">{t('home.language_label')}</legend>
          <div className="grid grid-cols-2 gap-2 sm:grid-cols-3">
            {LANGUAGES.map((l) => (
              <button
                key={l.code}
                type="button"
                lang={l.code}
                aria-pressed={language === l.code}
                onClick={() => setLanguage(l.code)}
                className={`min-h-tap rounded border px-4 text-left font-medium transition-colors ${
                  language === l.code
                    ? 'border-brand bg-brand-soft text-brand'
                    : 'border-line-strong bg-surface hover:bg-brand-soft'
                }`}
              >
                {l.name}
              </button>
            ))}
          </div>
        </fieldset>

        <div className="mt-8">
          <Link href="/assistant" className="btn-primary text-lg">
            {started ? t('home.resume') : t('home.start')}
            <ArrowRight aria-hidden className="h-5 w-5" />
          </Link>
        </div>
      </section>

      <section aria-labelledby="how">
        <h2 id="how" className="text-xl">{t('home.how_title')}</h2>
        <ol className="mt-5 divide-y divide-line border-y border-line">
          {steps.map((s, i) => (
            <li key={i} className="flex gap-4 py-5">
              <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full border border-line-strong text-sm font-semibold" aria-hidden>
                {i + 1}
              </span>
              <div>
                <h3 className="text-base">{s.title}</h3>
                <p className="mt-1 text-ink-muted">{s.text}</p>
              </div>
            </li>
          ))}
        </ol>
        <p className="mt-6 text-sm text-ink-muted">{t('home.privacy')}</p>
        {count !== null && <p className="mt-2 text-sm text-ink-muted">{t('home.coverage', { count })}</p>}
      </section>
    </main>
  );
}
