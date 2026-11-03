'use client';

import { useCallback, useEffect, useState } from 'react';
import Link from 'next/link';
import { ChevronRight } from 'lucide-react';
import { StatusIcon } from '@/components/StatusMark';
import { api, ApiError } from '@/lib/api';
import { STATUS_ORDER } from '@/lib/criteria';
import { useI18n } from '@/lib/i18n';
import { useSession } from '@/lib/session';
import type { EligibilityResponse } from '@/lib/types';

type Load = { state: 'loading' } | { state: 'error'; code: string } | { state: 'ok'; data: EligibilityResponse };

export default function SchemesPage() {
  const { t } = useI18n();
  const { citizen, hydrated } = useSession();
  const [load, setLoad] = useState<Load>({ state: 'loading' });
  const [showNot, setShowNot] = useState(false);

  const run = useCallback(() => {
    setLoad({ state: 'loading' });
    api
      .eligibility(citizen)
      .then((data) => setLoad({ state: 'ok', data }))
      .catch((e) => setLoad({ state: 'error', code: e instanceof ApiError ? e.code : 'generic' }));
    // The result depends on the language and the answers only.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [citizen.language, JSON.stringify(citizen.profile), JSON.stringify(citizen.skipped)]);

  useEffect(() => {
    if (hydrated) run();
  }, [hydrated, run]);

  return (
    <main id="main" className="mx-auto w-full max-w-4xl px-4 py-8 sm:px-6 sm:py-12">
      <h1 className="text-2xl sm:text-3xl">{t('results.title')}</h1>

      {load.state === 'loading' && (
        <p role="status" className="mt-8 text-ink-muted">
          {t('results.loading')}
        </p>
      )}

      {load.state === 'error' && (
        <div role="alert" className="mt-8 rounded border border-bad/30 bg-bad-soft p-4 text-bad">
          <p>{t(`error.${load.code}`)}</p>
          <button type="button" onClick={run} className="btn-secondary mt-3">
            {t('common.retry')}
          </button>
        </div>
      )}

      {load.state === 'ok' && !load.data.ready && (
        <section className="mt-8 border-y border-line py-8">
          <h2 className="text-xl">{t('results.gate_title')}</h2>
          <p className="mt-2 max-w-xl text-ink-muted">{t('results.gate_text')}</p>
          <Link href="/assistant" className="btn-primary mt-5">
            {t('results.gate_action')}
          </Link>
        </section>
      )}

      {load.state === 'ok' && load.data.ready && <Results data={load.data} showNot={showNot} setShowNot={setShowNot} />}
    </main>
  );
}

function Results({ data, showNot, setShowNot }: { data: EligibilityResponse; showNot: boolean; setShowNot: (v: boolean) => void }) {
  const { t } = useI18n();
  const groups = STATUS_ORDER.map((status) => ({ status, items: data.results.filter((r) => r.status === status) })).filter((g) => g.items.length);
  const canRefine = data.results.some((r) => r.status === 'insufficient_info');
  const notCount = groups.find((g) => g.status === 'not_eligible')?.items.length ?? 0;

  return (
    <>
      <p className="mt-2 text-ink-muted">{t('results.subtitle')}</p>
      <div className="mt-4 flex flex-wrap items-center gap-x-6 gap-y-2 text-sm text-ink-muted">
        <span>{t('results.checked', { count: data.results.length })}</span>
        {canRefine && (
          <Link href="/assistant" className="font-medium text-brand underline underline-offset-4">
            {t('results.refine')}
          </Link>
        )}
      </div>

      {!data.translated && (
        <p role="status" className="mt-4 rounded border border-warn/30 bg-warn-soft px-4 py-3 text-sm text-warn">
          {t('results.translation_notice')}
        </p>
      )}

      {groups.map(({ status, items }) => {
        if (status === 'not_eligible' && !showNot) return null;
        return (
          <section key={status} className="mt-10" aria-labelledby={`g-${status}`}>
            <div className="flex items-start gap-3">
              <StatusIcon status={status} className="mt-1 h-5 w-5" />
              <div>
                <h2 id={`g-${status}`} className="text-lg">
                  {t(`status.${status}`)}
                </h2>
                <p className="text-sm text-ink-muted">{t(`status_desc.${status}`)}</p>
              </div>
            </div>
            <ul className="mt-3 divide-y divide-line border-y border-line">
              {items.map((r) => (
                <li key={r.scheme_id}>
                  <Link href={`/schemes/${r.scheme_id}`} className="group flex items-start justify-between gap-4 py-4 hover:bg-brand-soft/60 sm:px-2">
                    <div className="min-w-0">
                      <h3 className="text-base font-semibold text-brand group-hover:underline">{r.scheme.name}</h3>
                      <p className="mt-0.5 text-sm text-ink-faint">{r.scheme.ministry}</p>
                      <p className="mt-2 text-ink-muted">{r.scheme.benefits}</p>
                      {r.status === 'insufficient_info' && r.missing_fields.length > 0 && (
                        <p className="mt-2 text-sm text-ink-muted">
                          {t('results.needs', { fields: r.missing_fields.map((f) => t(`field.${f}`)).join(', ') })}
                        </p>
                      )}
                    </div>
                    <span className="mt-1 flex shrink-0 items-center gap-1 text-sm font-medium text-brand">
                      <span className="hidden sm:inline">{t('results.view')}</span>
                      <ChevronRight aria-hidden className="h-5 w-5" />
                    </span>
                  </Link>
                </li>
              ))}
            </ul>
          </section>
        );
      })}

      {notCount > 0 && (
        <button type="button" onClick={() => setShowNot(!showNot)} aria-expanded={showNot} className="btn-secondary mt-8">
          {showNot ? t('results.hide_not_eligible') : t('results.show_not_eligible', { count: notCount })}
        </button>
      )}

      <p className="mt-10 text-sm text-ink-muted">{t('results.catalog_note')}</p>
    </>
  );
}
