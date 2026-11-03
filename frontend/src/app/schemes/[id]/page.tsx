'use client';

import { useCallback, useEffect, useState } from 'react';
import Link from 'next/link';
import { useParams } from 'next/navigation';
import { ArrowLeft, CircleAlert, CircleCheck, CircleHelp, CircleX, ExternalLink, ListChecks } from 'lucide-react';
import { DocumentChecklist } from '@/components/DocumentChecklist';
import { StatusIcon } from '@/components/StatusMark';
import { api, ApiError } from '@/lib/api';
import { useCriterionText } from '@/lib/criteria';
import { useI18n } from '@/lib/i18n';
import { useSession } from '@/lib/session';
import type { CriterionItem, DocStatus, Outcome, SchemeDetailResponse } from '@/lib/types';

type Load = { state: 'loading' } | { state: 'error'; code: string } | { state: 'ok'; data: SchemeDetailResponse };

const OUTCOME_ICON: Record<Outcome, { Icon: typeof CircleCheck; color: string }> = {
  met: { Icon: CircleCheck, color: 'text-ok' },
  unmet: { Icon: CircleX, color: 'text-bad' },
  unknown: { Icon: CircleHelp, color: 'text-brand' },
  verify: { Icon: CircleAlert, color: 'text-warn' },
};

export default function SchemeDetailPage() {
  const { id } = useParams<{ id: string }>();
  const { t } = useI18n();
  const criterionText = useCriterionText();
  const { citizen, hydrated } = useSession();
  const [load, setLoad] = useState<Load>({ state: 'loading' });

  const run = useCallback(() => {
    setLoad({ state: 'loading' });
    api
      .scheme(id, citizen)
      .then((data) => setLoad({ state: 'ok', data }))
      .catch((e) => setLoad({ state: 'error', code: e instanceof ApiError ? e.code : 'generic' }));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id, citizen.language, JSON.stringify(citizen.profile), JSON.stringify(citizen.skipped)]);

  useEffect(() => {
    if (hydrated) run();
  }, [hydrated, run]);

  const back = (
    <Link href="/schemes" className="-ml-2 inline-flex min-h-tap items-center gap-2 px-2 font-medium text-brand">
      <ArrowLeft aria-hidden className="h-5 w-5" />
      {t('detail.back')}
    </Link>
  );

  if (load.state === 'loading') {
    return (
      <main id="main" className="mx-auto w-full max-w-3xl px-4 py-8 sm:px-6">
        {back}
        <p role="status" className="mt-6 text-ink-muted">{t('common.loading')}</p>
      </main>
    );
  }
  if (load.state === 'error') {
    return (
      <main id="main" className="mx-auto w-full max-w-3xl px-4 py-8 sm:px-6">
        {back}
        <div role="alert" className="mt-6 rounded border border-bad/30 bg-bad-soft p-4 text-bad">
          <p>{t(`error.${load.code}`)}</p>
          {load.code !== 'not_found' && (
            <button type="button" onClick={run} className="btn-secondary mt-3">{t('common.retry')}</button>
          )}
        </div>
      </main>
    );
  }

  const { scheme, evaluation, ready, translated, document_status: docStatus } = load.data;
  const missingDocs = docStatus.filter((d) => d.status === 'missing' || d.status === 'expired').length;
  const verifyItems = evaluation.items.filter((i) => i.outcome === 'verify');
  const checkItems = evaluation.items.filter((i) => i.outcome !== 'verify');

  const renderItem = (item: CriterionItem, i: number) => {
    const { Icon, color } = OUTCOME_ICON[item.outcome];
    return (
      <li key={i} className="flex items-start gap-3 py-3">
        <Icon aria-hidden className={`mt-1 h-5 w-5 shrink-0 ${color}`} />
        <div>
          <p>{criterionText(item)}</p>
          {item.outcome === 'unknown' && item.field && (
            <div className="mt-1 flex flex-wrap items-center gap-x-3">
              {item.skipped && <span className="text-sm text-ink-muted">{t('detail.skipped_info')}</span>}
              <Link href="/check" className="inline-flex min-h-tap items-center text-sm font-medium text-brand underline underline-offset-4">
                {t('detail.provide_info')}
              </Link>
            </div>
          )}
        </div>
      </li>
    );
  };

  return (
    <main id="main" className="mx-auto w-full max-w-3xl px-4 py-8 sm:px-6 sm:py-10">
      {back}
      <h1 className="mt-4 text-2xl sm:text-3xl">{scheme.name}</h1>
      <p className="mt-1 text-ink-muted">
        {t('detail.issued_by')}: {scheme.ministry}
      </p>

      {!translated && (
        <p role="status" className="mt-4 rounded border border-warn/30 bg-warn-soft px-4 py-3 text-sm text-warn">
          {t('results.translation_notice')}
        </p>
      )}

      {ready ? (
        <div className="mt-6 flex items-start gap-3 border-y border-line py-4">
          <StatusIcon status={evaluation.status} className="mt-1 h-6 w-6" />
          <div>
            <p className="font-semibold">{t(`status.${evaluation.status}`)}</p>
            <p className="text-sm text-ink-muted">{t(`status_desc.${evaluation.status}`)}</p>
          </div>
        </div>
      ) : (
        <div className="mt-6 border-y border-line py-4">
          <p className="text-ink-muted">{t('detail.not_ready')}</p>
          <Link href="/assistant" className="btn-primary mt-3">{t('results.gate_action')}</Link>
        </div>
      )}

      <section className="mt-8" aria-labelledby="about">
        <h2 id="about" className="text-xl">{t('detail.about')}</h2>
        <p className="mt-2 text-ink-muted">{scheme.summary}</p>
        <h3 className="mt-5 text-base">{t('detail.benefits')}</h3>
        <p className="mt-1">{scheme.benefits}</p>
      </section>

      {ready && (
        <section className="mt-10" aria-labelledby="elig">
          <h2 id="elig" className="text-xl">{t('detail.eligibility')}</h2>
          <ul className="mt-2 divide-y divide-line border-y border-line">{checkItems.map(renderItem)}</ul>
          {verifyItems.length > 0 && (
            <>
              <h3 className="mt-6 text-base">{t('detail.verify')}</h3>
              <ul className="mt-1 divide-y divide-line border-y border-line">{verifyItems.map(renderItem)}</ul>
            </>
          )}
        </section>
      )}

      <section className="mt-10" aria-labelledby="docs">
        <h2 id="docs" className="text-xl">{t('detail.documents')}</h2>
        <div className="mt-2">
          <DocumentChecklist schemeId={scheme.id} documents={scheme.documents} status={docStatus.map((d) => d.status)} />
        </div>
        {docStatus.length > 0 && (
          <p className="mt-3 text-sm text-ink-muted">
            {missingDocs > 0 ? t('detail.docs_missing', { count: missingDocs }) : t('detail.docs_all')}{' '}
            <Link href="/vault" className="font-medium text-brand underline underline-offset-4">{t('detail.add_documents')}</Link>
          </p>
        )}
      </section>

      <section className="mt-10" aria-labelledby="apply">
        <h2 id="apply" className="text-xl">{t('detail.apply')}</h2>
        <ol className="mt-3 divide-y divide-line border-y border-line">
          {[
            { title: t('detail.step1_title'), text: t('detail.step1_text') },
            { title: t('detail.step2_title'), text: t('detail.step2_text') },
            {
              title: t('detail.step3_title'),
              text: scheme.apply.url ? t('detail.step3_with_url') : t('detail.step3_with_channel', { channel: scheme.apply.channel ?? '' }),
            },
          ].map((s, i) => (
            <li key={i} className="flex gap-4 py-4">
              <span aria-hidden className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full border border-line-strong text-sm font-semibold">
                {i + 1}
              </span>
              <div>
                <h3 className="text-base">{s.title}</h3>
                <p className="mt-1 text-ink-muted">{s.text}</p>
              </div>
            </li>
          ))}
        </ol>
        <Link href={`/guide?scheme=${scheme.id}`} className="btn-secondary mt-5 mr-3">
          <ListChecks aria-hidden className="h-5 w-5" />
          {t('detail.guide_me')}
        </Link>
        {scheme.apply.url && (
          <a href={scheme.apply.url} target="_blank" rel="noopener noreferrer" className="btn-primary mt-5">
            {t('detail.open_website')}
            <ExternalLink aria-hidden className="h-4 w-4" />
            <span className="sr-only">({t('common.open_new_tab')})</span>
          </a>
        )}
      </section>

      {scheme.notes.length > 0 && (
        <section className="mt-10" aria-labelledby="notes">
          <h2 id="notes" className="text-xl">{t('detail.notes')}</h2>
          <ul className="mt-2 list-disc space-y-2 pl-5 text-ink-muted">
            {scheme.notes.map((n, i) => <li key={i}>{n}</li>)}
          </ul>
        </section>
      )}

      <section className="mt-10 border-t border-line pt-6" aria-labelledby="source">
        <h2 id="source" className="text-base">{t('detail.source')}</h2>
        {scheme.source_url && (
          <a href={scheme.source_url} target="_blank" rel="noopener noreferrer" className="mt-1 inline-flex min-h-tap items-center gap-2 break-all font-medium text-brand underline underline-offset-4">
            {t('detail.source_open')}
            <ExternalLink aria-hidden className="h-4 w-4 shrink-0" />
            <span className="sr-only">({t('common.open_new_tab')})</span>
          </a>
        )}
        <p className="mt-2 text-sm text-ink-muted">{t('detail.verified_note')}</p>
      </section>
    </main>
  );
}
