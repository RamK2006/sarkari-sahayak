'use client';

import { useEffect, useState } from 'react';
import { useI18n } from '@/lib/i18n';

/** Checklist of documents; ticks are kept in this browser only, keyed by scheme and document position. */
export function DocumentChecklist({ schemeId, documents }: { schemeId: string; documents: string[] }) {
  const { t } = useI18n();
  const key = `sa.docs.${schemeId}`;
  const [done, setDone] = useState<number[]>([]);

  useEffect(() => {
    try {
      setDone(JSON.parse(localStorage.getItem(key) ?? '[]'));
    } catch {
      setDone([]);
    }
  }, [key]);

  const toggle = (i: number) => {
    const next = done.includes(i) ? done.filter((d) => d !== i) : [...done, i];
    setDone(next);
    try {
      localStorage.setItem(key, JSON.stringify(next));
    } catch {
      /* storage unavailable */
    }
  };

  return (
    <div>
      <p className="text-sm text-ink-muted">{t('detail.documents_hint')}</p>
      <p className="mt-1 text-sm font-medium" aria-live="polite">
        {t('detail.documents_progress', { done: done.filter((d) => d < documents.length).length, total: documents.length })}
      </p>
      <ul className="mt-3 divide-y divide-line border-y border-line">
        {documents.map((doc, i) => (
          <li key={i}>
            <label className="flex min-h-tap cursor-pointer items-start gap-3 py-3">
              <input
                type="checkbox"
                checked={done.includes(i)}
                onChange={() => toggle(i)}
                className="mt-1 h-5 w-5 shrink-0 accent-[var(--brand)]"
              />
              <span className={done.includes(i) ? 'text-ink-muted line-through' : ''}>{doc}</span>
            </label>
          </li>
        ))}
      </ul>
    </div>
  );
}
