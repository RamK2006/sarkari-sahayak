'use client';

import { useEffect, useState } from 'react';
import { useI18n } from '@/lib/i18n';
import type { DocStatus } from '@/lib/types';

/**
 * Required documents. Each shows whether it is already in the citizen's vault; documents that cannot be
 * recognised (photographs, mobile number) are ticked by hand. Ticks stay in this browser only.
 */
export function DocumentChecklist({ schemeId, documents, status }: { schemeId: string; documents: string[]; status: DocStatus[] }) {
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

  const ready = (i: number) => status[i] === 'have' || done.includes(i);

  return (
    <div>
      <p className="text-sm text-ink-muted">{t('detail.documents_hint')}</p>
      <p className="mt-1 text-sm font-medium" aria-live="polite">
        {t('detail.documents_progress', { done: documents.filter((_, i) => ready(i)).length, total: documents.length })}
      </p>
      <ul className="mt-3 divide-y divide-line border-y border-line">
        {documents.map((doc, i) => (
          <li key={i}>
            <label className="flex min-h-tap cursor-pointer items-start gap-3 py-3">
              <input
                type="checkbox"
                checked={ready(i)}
                disabled={status[i] === 'have'}
                onChange={() => toggle(i)}
                className="mt-1 h-5 w-5 shrink-0 accent-[var(--brand)]"
              />
              <span className="flex-1">
                <span className={ready(i) ? 'text-ink-muted line-through' : ''}>{doc}</span>
                <span className={`block text-sm ${status[i] === 'have' ? 'text-ok' : status[i] === 'expired' ? 'text-bad' : 'text-ink-faint'}`}>
                  {t(`detail.doc_${status[i]}`)}
                </span>
              </span>
            </label>
          </li>
        ))}
      </ul>
    </div>
  );
}
