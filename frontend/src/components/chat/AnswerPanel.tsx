'use client';

import { useI18n } from '@/lib/i18n';
import type { Question } from '@/lib/types';

interface Props {
  question: Question;
  disabled: boolean;
  onAnswer: (value: string | number | boolean) => void;
  onSkip: () => void;
}

/** Controls for the question currently being asked. Number answers go through the message box below. */
export function AnswerPanel({ question, disabled, onAnswer, onSkip }: Props) {
  const { t } = useI18n();
  const prompt = t(`q.${question.field}.prompt`);

  return (
    <div className="border-t border-line pt-3">
      {question.kind === 'choice' && (
        <div className="flex flex-wrap gap-2" role="group" aria-label={prompt}>
          {question.options!.map((o) => (
            <button key={o} type="button" disabled={disabled} onClick={() => onAnswer(o)} className="btn-secondary">
              {t(`opt.${question.field}.${o}`)}
            </button>
          ))}
        </div>
      )}

      {question.kind === 'boolean' && (
        <div className="flex gap-2" role="group" aria-label={prompt}>
          <button type="button" disabled={disabled} onClick={() => onAnswer(true)} className="btn-secondary min-w-[96px]">
            {t('common.yes')}
          </button>
          <button type="button" disabled={disabled} onClick={() => onAnswer(false)} className="btn-secondary min-w-[96px]">
            {t('common.no')}
          </button>
        </div>
      )}

      <div className="flex flex-wrap items-center gap-x-4 gap-y-1">
        {question.skippable && (
          <button type="button" disabled={disabled} onClick={onSkip} className="btn-quiet -ml-3">
            {t('chat.skip_question')}
          </button>
        )}
        <details className="text-sm text-ink-muted">
          <summary className="min-h-tap cursor-pointer select-none py-3 hover:text-ink">{t('chat.why')}</summary>
          <p className="pb-2">{t(`q.${question.field}.why`)}</p>
        </details>
      </div>
    </div>
  );
}
