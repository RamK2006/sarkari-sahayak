'use client';

import { useState, type FormEvent } from 'react';
import { Mic, Send, Square, Volume2, VolumeX } from 'lucide-react';
import { useI18n } from '@/lib/i18n';

interface Props {
  /** Set while a number is being asked for: the box then takes a numeric answer. */
  numeric: { hint: string | null } | null;
  disabled: boolean;
  recording: boolean;
  readAloud: boolean;
  onSend: (text: string) => void;
  onToggleRecording: () => void;
  onToggleReadAloud: () => void;
}

export function Composer({ numeric, disabled, recording, readAloud, onSend, onToggleRecording, onToggleReadAloud }: Props) {
  const { t } = useI18n();
  const [text, setText] = useState('');

  const submit = (e: FormEvent) => {
    e.preventDefault();
    const value = text.trim();
    if (!value || disabled) return;
    onSend(value);
    setText('');
  };

  return (
    <form onSubmit={submit} className="flex items-stretch gap-2 border-t border-line pt-3">
      <button
        type="button"
        onClick={onToggleReadAloud}
        aria-pressed={readAloud}
        aria-label={t(readAloud ? 'chat.read_aloud_on' : 'chat.read_aloud_off')}
        title={t(readAloud ? 'chat.read_aloud_on' : 'chat.read_aloud_off')}
        className={`btn min-w-tap shrink-0 px-0 ${readAloud ? 'border-brand bg-brand-soft text-brand' : 'border-line-strong bg-surface text-ink-muted hover:bg-brand-soft'}`}
      >
        {readAloud ? <Volume2 aria-hidden className="h-5 w-5" /> : <VolumeX aria-hidden className="h-5 w-5" />}
      </button>

      <label className="min-w-0 flex-1">
        <span className="sr-only">{t('chat.input_label')}</span>
        <input
          className="field"
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder={numeric?.hint ?? t('chat.input_placeholder')}
          inputMode={numeric ? 'numeric' : 'text'}
          maxLength={1000}
          autoComplete="off"
          disabled={disabled || recording}
        />
      </label>

      <button
        type="button"
        onClick={onToggleRecording}
        disabled={disabled && !recording}
        aria-pressed={recording}
        aria-label={t(recording ? 'chat.mic_stop' : 'chat.mic_start')}
        title={t(recording ? 'chat.mic_stop' : 'chat.mic_start')}
        className={`btn min-w-tap shrink-0 px-0 ${recording ? 'border-bad bg-bad text-white hover:bg-bad' : 'border-line-strong bg-surface hover:bg-brand-soft'}`}
      >
        {recording ? <Square aria-hidden className="h-5 w-5 fill-current" /> : <Mic aria-hidden className="h-5 w-5" />}
      </button>

      <button type="submit" disabled={disabled || recording || !text.trim()} className="btn-primary min-w-tap shrink-0 px-0 sm:px-5" aria-label={t('chat.send')}>
        <Send aria-hidden className="h-5 w-5" />
        <span className="hidden sm:inline">{t('chat.send')}</span>
      </button>
    </form>
  );
}
