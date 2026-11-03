'use client';

import { Suspense, useEffect, useMemo, useRef, useState } from 'react';
import { useSearchParams } from 'next/navigation';
import Link from 'next/link';
import { Bell, CircleAlert, CircleCheck, FileUp, Trash2 } from 'lucide-react';
import { api, ApiError } from '@/lib/api';
import { useI18n } from '@/lib/i18n';
import { useSession } from '@/lib/session';
import { reviewOf, useVault } from '@/lib/vault';
import type { ReviewState, VaultDoc } from '@/lib/types';

function useReviewText() {
  const { t, formatDate } = useI18n();
  return (doc: VaultDoc): { state: ReviewState; text: string } => {
    if (!doc.readable) return { state: 'no_expiry', text: t('review.unreadable') };
    const exp = doc.fields?.expiry_date ?? null;
    const { state, days } = reviewOf(exp);
    return { state, text: t(`review.${state}`, { date: exp ? formatDate(exp) : '', days: days ?? 0 }) };
  };
}

function DocCard({ doc }: { doc: VaultDoc }) {
  const { t, formatDate } = useI18n();
  const { update, remove } = useVault();
  const reviewText = useReviewText();
  const [location, setLocation] = useState(doc.location);
  const [purpose, setPurpose] = useState(doc.purpose);
  const [saved, setSaved] = useState(false);
  const review = reviewText(doc);
  const f = doc.fields;
  const attention = review.state === 'expired' || review.state === 'expiring_soon' || !doc.readable;

  return (
    <li className="rounded-lg border border-line bg-surface p-5">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h3 className="font-display text-lg">{t(`doctype.${doc.doc_type}`)}</h3>
          <p className="text-sm text-ink-faint">{doc.fileName}</p>
        </div>
        <button type="button" onClick={() => remove(doc.id)} className="btn-quiet min-w-tap px-0" aria-label={`${t('common.remove')}: ${t(`doctype.${doc.doc_type}`)}`}>
          <Trash2 aria-hidden className="h-5 w-5" />
        </button>
      </div>

      <p className={`mt-3 flex items-start gap-2 ${attention ? 'text-warn' : 'text-ok'}`}>
        {attention ? <CircleAlert aria-hidden className="mt-1 h-5 w-5 shrink-0" /> : <CircleCheck aria-hidden className="mt-1 h-5 w-5 shrink-0" />}
        <span>{review.text}</span>
      </p>
      {f?.quality_issues.map((q) => (
        <p key={q} className="mt-1 text-sm text-warn">{t(`quality.${q}`)}</p>
      ))}

      {f && (
        <dl className="mt-3 grid gap-x-6 gap-y-1 text-sm sm:grid-cols-2">
          {f.holder_name && (<><dt className="text-ink-faint">{t('vault.holder')}</dt><dd>{f.holder_name}</dd></>)}
          {f.date_of_birth && (<><dt className="text-ink-faint">{t('vault.dob')}</dt><dd>{formatDate(f.date_of_birth)}</dd></>)}
          {f.issuer && (<><dt className="text-ink-faint">{t('vault.issuer')}</dt><dd>{f.issuer}</dd></>)}
          {f.id_last4 && (<><dt className="text-ink-faint">{t('vault.id_ends')}</dt><dd>{f.id_last4}</dd></>)}
        </dl>
      )}

      <form
        className="mt-4 grid gap-3 sm:grid-cols-2"
        onSubmit={(e) => {
          e.preventDefault();
          update(doc.id, { location: location.trim(), purpose: purpose.trim() });
          setSaved(true);
        }}
      >
        <div>
          <label htmlFor={`loc-${doc.id}`} className="mb-1 block text-sm font-medium">{t('vault.where')}</label>
          <input id={`loc-${doc.id}`} className="field" value={location} maxLength={120} placeholder={t('vault.where_placeholder')} onChange={(e) => { setLocation(e.target.value); setSaved(false); }} />
        </div>
        <div>
          <label htmlFor={`pur-${doc.id}`} className="mb-1 block text-sm font-medium">{t('vault.purpose')}</label>
          <input id={`pur-${doc.id}`} className="field" value={purpose} maxLength={120} placeholder={t('vault.purpose_placeholder')} onChange={(e) => { setPurpose(e.target.value); setSaved(false); }} />
        </div>
        <div className="flex items-center gap-3 sm:col-span-2">
          <button type="submit" className="btn-secondary">{t('common.save')}</button>
          {saved && <span role="status" className="text-sm text-ok">{t('vault.saved')}</span>}
        </div>
      </form>
    </li>
  );
}

function VaultInner() {
  const { t, language, formatDate } = useI18n();
  const { docs, add, hydrated } = useVault();
  const { setFacts } = useSession();
  const params = useSearchParams();
  const wanted = params.get('type');
  const reviewText = useReviewText();

  const input = useRef<HTMLInputElement>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [info, setInfo] = useState<string | null>(null);
  const [query, setQuery] = useState('');
  const [perm, setPerm] = useState<NotificationPermission | 'unsupported'>('default');

  useEffect(() => {
    setPerm(typeof Notification === 'undefined' ? 'unsupported' : Notification.permission);
  }, []);

  const upload = async (file: File) => {
    setBusy(true);
    setError(null);
    setInfo(null);
    try {
      const res = await api.analyzeDocument(file);
      add({
        id: `d${Date.now().toString(36)}`, doc_type: res.doc_type, readable: res.readable, fields: res.fields,
        fileName: file.name, addedAt: new Date().toISOString(), location: '', purpose: '',
      });
      if (res.profile_hints.age !== undefined) {
        setFacts({ age: res.profile_hints.age });
        setInfo(t('vault.age_applied', { age: res.profile_hints.age }));
      }
    } catch (e) {
      setError(e instanceof ApiError ? e.code : 'generic');
    } finally {
      setBusy(false);
      if (input.current) input.current.value = '';
    }
  };

  // Renewals that need attention, soonest first.
  const due = useMemo(
    () =>
      docs
        .map((d) => ({ d, r: reviewOf(d.fields?.expiry_date) }))
        .filter(({ r }) => r.state === 'expired' || r.state === 'expiring_soon' || r.state === 'upcoming')
        .sort((a, b) => (a.r.days ?? 0) - (b.r.days ?? 0)),
    [docs],
  );

  // Notify once per day per document while permission is granted.
  useEffect(() => {
    if (!hydrated || perm !== 'granted') return;
    const today = new Date().toISOString().slice(0, 10);
    due.forEach(({ d }) => {
      const key = `sa.notified.${d.id}.${today}`;
      try {
        if (localStorage.getItem(key)) return;
        localStorage.setItem(key, '1');
      } catch {
        return;
      }
      new Notification(t('notify.title'), { body: `${t(`doctype.${d.doc_type}`)}: ${reviewText(d).text}` });
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [hydrated, perm, due, language]);

  const shown = docs.filter((d) => {
    const q = query.trim().toLowerCase();
    if (!q) return true;
    return [t(`doctype.${d.doc_type}`), d.location, d.purpose, d.fields?.holder_name ?? '', d.fileName].some((s) => s.toLowerCase().includes(q));
  });

  return (
    <main id="main" className="mx-auto w-full max-w-4xl px-4 py-8 sm:px-6 sm:py-10">
      <h1 className="text-3xl">{t('vault.title')}</h1>
      <p className="mt-2 max-w-2xl text-ink-muted">{t('vault.subtitle')}</p>

      <section className="mt-8 rounded-lg border border-dashed border-line-strong bg-surface p-6" aria-labelledby="up">
        <h2 id="up" className="text-lg">{wanted ? t('vault.upload_wanted', { doc: t(`doctype.${wanted}`) }) : t('vault.upload')}</h2>
        <p className="mt-1 text-sm text-ink-muted">{t('vault.upload_hint')}</p>
        <input
          ref={input}
          type="file"
          accept="application/pdf,image/png,image/jpeg"
          className="sr-only"
          id="file"
          onChange={(e) => e.target.files?.[0] && upload(e.target.files[0])}
        />
        <label htmlFor="file" className={`btn-primary mt-4 cursor-pointer ${busy ? 'pointer-events-none opacity-60' : ''}`}>
          <FileUp aria-hidden className="h-5 w-5" />
          {busy ? t('vault.reading') : t('vault.choose_file')}
        </label>
        {busy && <p role="status" className="mt-3 text-ink-muted">{t('vault.reading')}</p>}
        {error && <p role="alert" className="mt-3 text-bad">{t(`error.${error}`)}</p>}
        {info && <p role="status" className="mt-3 text-ok">{info}</p>}
      </section>

      <section className="mt-10" aria-labelledby="rem">
        <h2 id="rem" className="text-xl">{t('vault.reminders_title')}</h2>
        {due.length === 0 ? (
          <p className="mt-2 text-ink-muted">{t('vault.reminders_empty')}</p>
        ) : (
          <ul className="mt-3 divide-y divide-line border-y border-line">
            {due.map(({ d }) => (
              <li key={d.id} className="flex items-start gap-3 py-3">
                <Bell aria-hidden className="mt-1 h-5 w-5 shrink-0 text-warn" />
                <div>
                  <p className="font-semibold">{t(`doctype.${d.doc_type}`)}</p>
                  <p className="text-ink-muted">{reviewText(d).text}</p>
                  {d.fields?.expiry_date && <p className="text-sm text-ink-faint">{formatDate(d.fields.expiry_date)}</p>}
                </div>
              </li>
            ))}
          </ul>
        )}
        {perm === 'default' && (
          <button type="button" className="btn-secondary mt-4" onClick={async () => setPerm(await Notification.requestPermission())}>
            {t('vault.notify_enable')}
          </button>
        )}
        {perm === 'granted' && <p className="mt-3 text-sm text-ok">{t('vault.notify_on')}</p>}
        {perm === 'denied' && <p className="mt-3 text-sm text-warn">{t('vault.notify_denied')}</p>}
      </section>

      <section className="mt-10" aria-labelledby="docs">
        <div className="flex flex-wrap items-end justify-between gap-4">
          <h2 id="docs" className="text-xl">{t('vault.title')}</h2>
          {docs.length > 0 && (
            <div className="w-full max-w-sm">
              <label htmlFor="find" className="sr-only">{t('vault.find')}</label>
              <input id="find" className="field" value={query} onChange={(e) => setQuery(e.target.value)} placeholder={t('vault.find')} />
            </div>
          )}
        </div>
        {docs.length === 0 ? (
          <p className="mt-3 text-ink-muted">{t('vault.empty')}</p>
        ) : (
          <>
            <ul className="mt-4 space-y-4">{shown.map((d) => <DocCard key={d.id} doc={d} />)}</ul>
            <Link href="/schemes" className="btn-primary mt-6">{t('vault.check_schemes')}</Link>
          </>
        )}
      </section>
    </main>
  );
}

export default function VaultPage() {
  return (
    <Suspense fallback={null}>
      <VaultInner />
    </Suspense>
  );
}
