'use client';

import { useEffect, useRef, useState } from 'react';
import Link from 'next/link';
import { ArrowRight, FileText, Keyboard, ListChecks, Phone, Search } from 'lucide-react';
import { Avatar } from '@/components/Avatar';
import { api } from '@/lib/api';
import { useI18n } from '@/lib/i18n';
import { LANGUAGES } from '@/lib/languages';

const ENTRIES = [
  { href: '/talk', key: 'talk', Icon: Phone },
  { href: '/khoj', key: 'khoj', Icon: Search },
  { href: '/check', key: 'check', Icon: ListChecks },
  { href: '/vault', key: 'vault', Icon: FileText },
] as const;

export default function Home() {
  const { t, language, setLanguage } = useI18n();
  const [count, setCount] = useState<number | null>(null);
  const [wave, setWave] = useState({ value: 'namaste' as const, key: 1 });
  const level = useRef(0);

  useEffect(() => {
    api.meta().then((m) => setCount(m.scheme_count)).catch(() => setCount(null));
  }, []);
  useEffect(() => setWave((w) => ({ ...w, key: w.key + 1 })), [language]);

  return (
    <main id="main">
      <section className="border-b border-line">
        <div className="mx-auto grid max-w-6xl items-center gap-8 px-4 py-10 sm:px-6 md:grid-cols-[1.2fr_1fr] lg:py-16">
          <div>
            <h1 className="text-4xl sm:text-5xl">{t('home.title')}</h1>
            <p className="mt-5 max-w-xl text-lg text-ink-muted">{t('home.subtitle')}</p>
            <div className="mt-8 flex flex-wrap gap-3">
              <Link href="/talk" className="btn-primary text-lg">
                <Phone aria-hidden className="h-5 w-5" />
                {t('home.start_call')}
              </Link>
              <Link href="/talk" onClick={() => { try { localStorage.setItem('sa.mode', 'chat'); } catch { /* ignore */ } }} className="btn-secondary text-lg">
                <Keyboard aria-hidden className="h-5 w-5" />
                {t('home.start_chat')}
              </Link>
            </div>
          </div>
          <div className="mx-auto w-full max-w-[360px]">
            <Avatar language={language} state="idle" mood="happy" gesture={wave} level={level} />
          </div>
        </div>
      </section>

      <section className="mx-auto max-w-6xl px-4 py-10 sm:px-6" aria-labelledby="lang">
        <h2 id="lang" className="text-xl">{t('home.language_label')}</h2>
        <div className="mt-4 grid grid-cols-2 gap-2 sm:grid-cols-4 lg:grid-cols-6">
          {LANGUAGES.map((l) => (
            <button
              key={l.code}
              type="button"
              lang={l.code}
              aria-pressed={language === l.code}
              onClick={() => setLanguage(l.code)}
              className={`min-h-tap rounded border px-3 text-left font-medium transition-colors ${
                language === l.code ? 'border-brand bg-brand-soft text-brand' : 'border-line-strong bg-surface hover:bg-brand-soft'
              }`}
            >
              {l.name}
            </button>
          ))}
        </div>
      </section>

      <section className="border-y border-line bg-surface" aria-labelledby="what">
        <div className="mx-auto max-w-6xl px-4 py-10 sm:px-6">
          <h2 id="what" className="sr-only">{t('home.how_title')}</h2>
          <ul className="grid gap-px overflow-hidden rounded-lg border border-line bg-line sm:grid-cols-2">
            {ENTRIES.map(({ href, key, Icon }, i) => (
              <li key={key} className="bg-surface">
                <Link href={href} className="group flex h-full items-start gap-4 p-6 hover:bg-brand-soft">
                  <span className="font-display text-4xl font-semibold text-accent" aria-hidden>{i + 1}</span>
                  <span className="flex-1">
                    <span className="flex items-center gap-2 font-display text-xl font-semibold">
                      <Icon aria-hidden className="h-5 w-5 text-brand" />
                      {t(`home.${key}_title`)}
                    </span>
                    <span className="mt-1 block text-ink-muted">{t(`home.${key}_text`)}</span>
                  </span>
                  <ArrowRight aria-hidden className="mt-2 h-5 w-5 text-brand transition-transform group-hover:translate-x-1" />
                </Link>
              </li>
            ))}
          </ul>
        </div>
      </section>

      <section className="mx-auto max-w-6xl space-y-2 px-4 py-8 text-sm text-ink-muted sm:px-6">
        <p>{t('home.privacy')}</p>
        {count !== null && <p>{t('home.coverage', { count })}</p>}
      </section>
    </main>
  );
}
