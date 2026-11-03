'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useI18n } from '@/lib/i18n';
import { useSession } from '@/lib/session';
import type { Profile } from '@/lib/types';

type Kind = 'number' | 'choice' | 'boolean';
interface Field {
  name: string;
  kind: Kind;
  options?: string[];
  max?: number;
}

// The five short steps. Field definitions mirror the backend registry; validation is repeated there.
const STEPS: Field[][] = [
  [{ name: 'age', kind: 'number', max: 120 }, { name: 'gender', kind: 'choice', options: ['female', 'male', 'other'] }],
  [
    { name: 'area', kind: 'choice', options: ['rural', 'urban'] },
    { name: 'occupation', kind: 'choice', options: ['farmer', 'student', 'labourer', 'self_employed', 'salaried', 'unemployed', 'homemaker', 'street_vendor', 'artisan', 'other'] },
  ],
  [{ name: 'annual_income', kind: 'number', max: 1_000_000_000 }, { name: 'category', kind: 'choice', options: ['general', 'obc', 'sc', 'st'] }],
  [{ name: 'priority_household', kind: 'boolean' }, { name: 'owns_farmland', kind: 'boolean' }],
  [{ name: 'pays_income_tax', kind: 'boolean' }, { name: 'govt_employee', kind: 'boolean' }],
];

export default function CheckPage() {
  const { t } = useI18n();
  const router = useRouter();
  const { profile, setFacts } = useSession();
  const [step, setStep] = useState(0);
  const [draft, setDraft] = useState<Record<string, string>>(() =>
    Object.fromEntries(Object.entries(profile).map(([k, v]) => [k, String(v)])),
  );
  const [invalid, setInvalid] = useState<string[]>([]);

  const fields = STEPS[step];
  const last = step === STEPS.length - 1;

  const commit = (): boolean => {
    const facts: Profile = {};
    const skip: string[] = [];
    const bad: string[] = [];
    for (const f of fields) {
      const raw = (draft[f.name] ?? '').trim();
      if (!raw) {
        skip.push(f.name);
      } else if (f.kind === 'number') {
        const n = Number(raw.replace(/[, ]/g, ''));
        if (!Number.isFinite(n) || n < 0 || n > (f.max ?? Infinity)) bad.push(f.name);
        else facts[f.name] = Math.round(n);
      } else if (f.kind === 'boolean') facts[f.name] = raw === 'true';
      else facts[f.name] = raw;
    }
    setInvalid(bad);
    if (bad.length) return false;
    setFacts(facts, skip);
    return true;
  };

  const next = () => {
    if (!commit()) return;
    if (last) router.push('/schemes');
    else setStep(step + 1);
  };

  return (
    <main id="main" className="mx-auto w-full max-w-2xl px-4 py-8 sm:px-6 sm:py-12">
      <h1 className="text-3xl">{t('check.title')}</h1>
      <p className="mt-2 text-ink-muted">{t('check.subtitle')}</p>

      <div className="mt-6 flex gap-1" aria-hidden>
        {STEPS.map((_, i) => (
          <span key={i} className={`h-1.5 flex-1 rounded-full ${i <= step ? 'bg-brand' : 'bg-line-strong'}`} />
        ))}
      </div>
      <p className="mt-2 text-sm font-medium text-ink-muted" aria-live="polite">{t('check.step', { current: step + 1, total: STEPS.length })}</p>

      <form onSubmit={(e) => { e.preventDefault(); next(); }} className="mt-6 space-y-8" noValidate>
        {fields.map((f) => (
          <fieldset key={f.name}>
            <legend className="text-lg font-semibold">{t(`q.${f.name}.prompt`)}</legend>
            <p className="mt-1 text-sm text-ink-muted">{t(`q.${f.name}.why`)}</p>
            {f.kind === 'number' ? (
              <div className="mt-3">
                <input
                  className="field max-w-xs"
                  inputMode="numeric"
                  value={draft[f.name] ?? ''}
                  aria-invalid={invalid.includes(f.name)}
                  aria-label={t(`q.${f.name}.prompt`)}
                  onChange={(e) => setDraft((d) => ({ ...d, [f.name]: e.target.value }))}
                />
                {invalid.includes(f.name) && <p role="alert" className="mt-1 text-sm text-bad">{t('check.number_invalid')}</p>}
                {t(`q.${f.name}.hint`) !== `q.${f.name}.hint` && <p className="mt-1 text-sm text-ink-muted">{t(`q.${f.name}.hint`)}</p>}
              </div>
            ) : (
              <div className="mt-3 flex flex-wrap gap-2" role="radiogroup" aria-label={t(`q.${f.name}.prompt`)}>
                {(f.kind === 'boolean' ? ['true', 'false'] : f.options!).map((o) => (
                  <button
                    key={o}
                    type="button"
                    role="radio"
                    aria-checked={draft[f.name] === o}
                    onClick={() => setDraft((d) => ({ ...d, [f.name]: d[f.name] === o ? '' : o }))}
                    className={`btn ${draft[f.name] === o ? 'border-brand bg-brand-soft text-brand' : 'border-line-strong bg-surface hover:bg-brand-soft'}`}
                  >
                    {f.kind === 'boolean' ? t(o === 'true' ? 'common.yes' : 'common.no') : t(`opt.${f.name}.${o}`)}
                  </button>
                ))}
              </div>
            )}
          </fieldset>
        ))}
        <p className="text-sm text-ink-muted">{t('check.skip_note')}</p>
        <div className="flex gap-3">
          {step > 0 && (
            <button type="button" className="btn-secondary" onClick={() => setStep(step - 1)}>
              {t('common.back')}
            </button>
          )}
          <button type="submit" className="btn-primary">
            {last ? t('check.see_results') : t('common.next')}
          </button>
        </div>
      </form>
    </main>
  );
}
