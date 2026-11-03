'use client';

import { useEffect, useRef } from 'react';
import { useI18n } from '@/lib/i18n';
import type { Message } from '@/lib/types';

/** Plain text of a message in the current language (also used for reading aloud). */
export function useMessageText() {
  const { t, formatNumber } = useI18n();
  return (m: Message): string => {
    switch (m.kind) {
      case 'greeting':
        return `${t('chat.greeting')} ${t('chat.skip_note')}`;
      case 'question':
        return t(`q.${m.field}.prompt`);
      case 'all_done':
        return t('chat.all_done');
      case 'error':
        return t(`error.${m.code}`);
      case 'text':
        return m.text;
      case 'answer': {
        if (m.value === null) return t('chat.answered_skipped');
        if (typeof m.value === 'boolean') return t(m.value ? 'common.yes' : 'common.no');
        if (typeof m.value === 'number') {
          const value = formatNumber(m.value);
          if (m.field === 'age') return t('ans.years', { value });
          if (m.field === 'annual_income') return t('ans.income', { value });
          return t('ans.count', { value });
        }
        return t(`opt.${m.field}.${m.value}`);
      }
    }
  };
}

interface Props {
  messages: Message[];
  working: string | null;
}

export function MessageList({ messages, working }: Props) {
  const { t } = useI18n();
  const text = useMessageText();
  const end = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const smooth = !window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    end.current?.scrollIntoView({ behavior: smooth ? 'smooth' : 'auto', block: 'end' });
  }, [messages.length, working]);

  return (
    <div role="region" className="min-h-0 flex-1 overflow-y-auto overscroll-contain" tabIndex={0} aria-label={t('chat.messages_label')}>
      <ol role="log" aria-live="polite" className="flex min-h-full flex-col justify-end gap-3 py-4 pr-1">
        {messages.map((m) => {
          const mine = m.role === 'user';
          const skipped = m.kind === 'answer' && m.value === null;
          return (
            <li key={m.id} className={`flex ${mine ? 'justify-end' : 'justify-start'}`}>
              <div
                className={`max-w-[88%] whitespace-pre-line rounded-lg px-4 py-3 sm:max-w-[75%] ${
                  mine
                    ? 'bg-brand text-white'
                    : m.kind === 'error'
                      ? 'border border-bad/30 bg-bad-soft text-bad'
                      : 'border border-line bg-surface text-ink'
                } ${skipped ? 'italic opacity-90' : ''}`}
              >
                <span className="sr-only">{mine ? t('chat.you') : t('chat.assistant')}: </span>
                {text(m)}
              </div>
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
