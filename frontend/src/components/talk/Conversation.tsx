'use client';

import { useEffect, useRef, useState } from 'react';
import Link from 'next/link';
import { FileUp, ListChecks } from 'lucide-react';
import { SchemeLine } from '@/components/SchemeLine';
import { api } from '@/lib/api';
import { useI18n } from '@/lib/i18n';
import { useSession } from '@/lib/session';
import type { Message, SchemeBrief, Status } from '@/lib/types';

/** A scheme the assistant mentioned, fetched in the current language so it never goes stale after a language switch. */
function SchemeRef({ id }: { id: string }) {
  const { citizen } = useSession();
  const [data, setData] = useState<{ scheme: SchemeBrief; status: Status } | null>(null);
  useEffect(() => {
    let live = true;
    api.scheme(id, citizen).then((r) => live && setData({ scheme: r.scheme, status: r.evaluation.status })).catch(() => undefined);
    return () => {
      live = false;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id, citizen.language, JSON.stringify(citizen.profile)]);
  return data ? <SchemeLine scheme={data.scheme} status={data.status} /> : null;
}

export function Conversation({ messages, working }: { messages: Message[]; working: string | null }) {
  const { t } = useI18n();
  const end = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const smooth = !window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    end.current?.scrollIntoView({ behavior: smooth ? 'smooth' : 'auto', block: 'end' });
  }, [messages.length, working]);

  return (
    <div role="region" className="min-h-0 flex-1 overflow-y-auto overscroll-contain" tabIndex={0} aria-label={t('chat.messages_label')}>
      <ol role="log" aria-live="polite" className="flex min-h-full flex-col justify-end gap-3 py-4 pr-1">
        {messages.length === 0 && (
          <li className="max-w-[88%] rounded-lg border border-line bg-surface px-4 py-3 text-lg sm:max-w-[75%]">{t('talk.greeting')}</li>
        )}
        {messages.map((m) => {
          if (m.kind === 'greeting') return null;
          const mine = m.role === 'user';
          return (
            <li key={m.id} className={`flex flex-col gap-2 ${mine ? 'items-end' : 'items-start'}`}>
              <div
                className={`max-w-[88%] whitespace-pre-line rounded-lg px-4 py-3 sm:max-w-[75%] ${
                  mine ? 'bg-brand text-onbrand' : m.kind === 'error' ? 'border border-bad/30 bg-bad-soft text-bad' : 'border border-line bg-surface text-ink'
                }`}
              >
                <span className="sr-only">{mine ? t('chat.you') : t('chat.assistant')}: </span>
                {m.kind === 'error' ? t(`error.${m.code}`) : m.text}
              </div>

              {m.kind === 'text' && m.role === 'assistant' && (
                <>
                  {m.schemes.length > 0 && (
                    <div className="w-full max-w-[88%] sm:max-w-[75%]">
                      <p className="mb-1 text-sm font-medium text-ink-muted">{t('talk.schemes_found')}</p>
                      <ul className="divide-y divide-line rounded-lg border border-line bg-surface px-2">
                        {m.schemes.map((id) => (
                          <li key={id}>
                            <SchemeRef id={id} />
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                  <div className="flex flex-wrap gap-2">
                    {m.guide && (
                      <Link href={`/guide?goal=${encodeURIComponent(m.guide)}`} className="btn-secondary">
                        <ListChecks aria-hidden className="h-5 w-5" />
                        {t('talk.guide_offer')}
                      </Link>
                    )}
                    {m.upload && (
                      <Link href={`/vault?type=${encodeURIComponent(m.upload)}`} className="btn-secondary">
                        <FileUp aria-hidden className="h-5 w-5" />
                        {t('talk.upload_suggest', { doc: t(`doctype.${m.upload}`) })}
                      </Link>
                    )}
                  </div>
                </>
              )}
            </li>
          );
        })}
        {working && (
          <li className="flex justify-start" aria-live="polite">
            <div className="flex items-center gap-3 rounded-lg border border-line bg-surface px-4 py-3 text-ink-muted">
              <span className="flex gap-1" aria-hidden>
                {[0, 150, 300].map((d) => (
                  <span key={d} className="h-1.5 w-1.5 animate-pulse rounded-full bg-ink-faint" style={{ animationDelay: `${d}ms` }} />
                ))}
              </span>
              {working}
            </div>
          </li>
        )}
        <div ref={end} />
      </ol>
    </div>
  );
}
