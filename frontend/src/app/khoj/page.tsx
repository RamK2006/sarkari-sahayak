'use client';

import { useCallback, useEffect, useState, type FormEvent } from 'react';
import { Search } from 'lucide-react';
import { SchemeLine } from '@/components/SchemeLine';
import { api, ApiError } from '@/lib/api';
import { useI18n } from '@/lib/i18n';
import type { Profile, SearchResponse } from '@/lib/types';

interface Form {
  query: string;
  state: string;
  age: string;
  gender: string;
  income: string;
  category: string;
  land: string;
}
const EMPTY: Form = { query: '', state: '', age: '', gender: '', income: '', category: '', land: '' };

export default function KhojPage() {
  const { t, language } = useI18n();
  const [form, setForm] = useState<Form>(EMPTY);
  const [states, setStates] = useState<{ value: string; label: string }[]>([]);
  const [result, setResult] = useState<SearchResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const run = useCallback(
    async (f: Form) => {
      setLoading(true);
      setError(null);
      const filters: Profile = {};
      if (f.age) filters.age = Number(f.age);
      if (f.gender) filters.gender = f.gender;
      if (f.income) filters.annual_income = Number(f.income.replace(/[, ]/g, ''));
      if (f.category) filters.category = f.category;
      if (f.land) filters.owns_farmland = f.land === 'yes';
      try {
        setResult(await api.search({ language, query: f.query, state: f.state || null, filters, limit: 30 }));
      } catch (e) {
        setError(e instanceof ApiError ? e.code : 'generic');
      } finally {
        setLoading(false);
      }
    },
    [language],
  );

  useEffect(() => {
    run(form);
    api.states(language).then((s) => setStates(s.states)).catch(() => setStates([]));
    // Reload in the new language; filters stay as they are.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [language]);

  const set = (k: keyof Form) => (e: { target: { value: string } }) => setForm((f) => ({ ...f, [k]: e.target.value }));
  const submit = (e: FormEvent) => {
    e.preventDefault();
    run(form);
  };
  const clear = () => {
    setForm(EMPTY);
    run(EMPTY);
  };

  const select = (id: string, label: string, value: string, onChange: (e: { target: { value: string } }) => void, options: [string, string][]) => (
    <div>
      <label htmlFor={id} className="mb-1 block text-sm font-medium">{label}</label>
      <select id={id} value={value} onChange={onChange} className="field">
        <option value="">{t('khoj.any')}</option>
        {options.map(([v, l]) => (
          <option key={v} value={v}>{l}</option>
        ))}
      </select>
    </div>
  );

  return (
    <main id="main" className="mx-auto w-full max-w-6xl px-4 py-8 sm:px-6 sm:py-10">
      <h1 className="text-3xl">{t('khoj.title')}</h1>
      <p className="mt-2 max-w-2xl text-ink-muted">{t('khoj.subtitle')}</p>

      <div className="mt-8 grid gap-8 lg:grid-cols-[320px_1fr]">
        <form onSubmit={submit} className="space-y-4 self-start rounded-lg border border-line bg-surface p-5" aria-label={t('khoj.filters')}>
          <div>
            <label htmlFor="q" className="mb-1 block text-sm font-medium">{t('common.search')}</label>
            <input id="q" className="field" value={form.query} onChange={set('query')} placeholder={t('khoj.search_placeholder')} maxLength={200} />
          </div>
          {select('state', t('khoj.state'), form.state, set('state'), states.map((s) => [s.value, s.label]))}
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label htmlFor="age" className="mb-1 block text-sm font-medium">{t('field.age')}</label>
              <input id="age" className="field" inputMode="numeric" value={form.age} onChange={set('age')} maxLength={3} />
            </div>
            {select('gender', t('field.gender'), form.gender, set('gender'), ['female', 'male', 'other'].map((g) => [g, t(`opt.gender.${g}`)]))}
          </div>
          <div>
            <label htmlFor="income" className="mb-1 block text-sm font-medium">{t('khoj.income')}</label>
            <input id="income" className="field" inputMode="numeric" value={form.income} onChange={set('income')} maxLength={12} />
          </div>
          {select('category', t('field.category'), form.category, set('category'), ['general', 'obc', 'sc', 'st'].map((c) => [c, t(`opt.category.${c}`)]))}
          {select('land', t('khoj.land'), form.land, set('land'), [['yes', t('common.yes')], ['no', t('common.no')]])}
          <div className="flex gap-2">
            <button type="submit" className="btn-primary flex-1">
              <Search aria-hidden className="h-5 w-5" />
              {t('common.search')}
            </button>
            <button type="button" onClick={clear} className="btn-secondary">{t('khoj.clear')}</button>
          </div>
        </form>

        <section aria-live="polite" aria-busy={loading}>
          {error && <p role="alert" className="rounded border border-bad/30 bg-bad-soft p-4 text-bad">{t(`error.${error}`)}</p>}
          {loading && !result && <p className="text-ink-muted">{t('common.loading')}</p>}
          {result && (
            <>
              <p className="text-sm text-ink-muted">
                {t('khoj.results_count', { count: result.results.length })} · {t('khoj.catalog_note', { count: result.total_catalog })}
              </p>
              {!result.translated && <p role="status" className="mt-3 rounded border border-warn/30 bg-warn-soft px-4 py-3 text-sm text-warn">{t('results.translation_notice')}</p>}
              {result.results.length === 0 ? (
                <p className="mt-6 text-ink-muted">{t('khoj.empty')}</p>
              ) : (
                <ul className="mt-3 divide-y divide-line border-y border-line">
                  {result.results.map((r) => (
                    <li key={r.scheme.id}>
                      <SchemeLine scheme={r.scheme} status={r.status} />
                    </li>
                  ))}
                </ul>
              )}
            </>
          )}
        </section>
      </div>
    </main>
  );
}
