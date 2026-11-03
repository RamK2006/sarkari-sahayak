'use client';

import { useCallback, useEffect, useRef, useState } from 'react';
import Link from 'next/link';
import { ArrowRight, RotateCcw, X } from 'lucide-react';
import { Avatar, type AvatarState } from '@/components/Avatar';
import { AnswerPanel } from '@/components/chat/AnswerPanel';
import { Composer } from '@/components/chat/Composer';
import { MessageList, useMessageText } from '@/components/chat/MessageList';
import { useRecorder } from '@/hooks/useRecorder';
import { useSpeech } from '@/hooks/useSpeech';
import { api, ApiError } from '@/lib/api';
import { useI18n, type Params } from '@/lib/i18n';
import { useSession } from '@/lib/session';

export default function AssistantPage() {
  const { t, language, formatNumber } = useI18n();
  const session = useSession();
  const messageText = useMessageText();

  const [readAloud, setReadAloud] = useState(false);
  const [transcribing, setTranscribing] = useState(false);
  const [notice, setNotice] = useState<{ key: string; params?: Params } | null>(null);
  const [confirmRestart, setConfirmRestart] = useState(false);

  const speech = useSpeech(useCallback(() => setNotice({ key: 'chat.speak_failed' }), []));

  const onRecorded = useCallback(
    async (audio: Blob) => {
      setTranscribing(true);
      try {
        const transcript = await api.transcribe(audio, language);
        if (!transcript) {
          setNotice({ key: 'chat.no_speech' });
          return;
        }
        setReadAloud(true); // a spoken question gets a spoken reply
        await session.sendText(transcript);
      } catch (e) {
        setNotice({ key: `error.${e instanceof ApiError ? e.code : 'generic'}` });
      } finally {
        setTranscribing(false);
      }
    },
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [language, session.sendText],
  );

  const recorder = useRecorder(onRecorded, (code) => setNotice({ key: code === 'mic_denied' ? 'chat.mic_denied' : 'chat.mic_unsupported' }));

  // Read each new assistant message aloud when the user has turned that on.
  const lastSpoken = useRef<string | null>(null);
  const last = [...session.messages].reverse().find((m) => m.role === 'assistant' && m.kind !== 'error');
  useEffect(() => {
    if (!last || !session.hydrated) return;
    if (lastSpoken.current === null) {
      lastSpoken.current = last.id; // do not speak history on first load
      return;
    }
    if (last.id === lastSpoken.current) return;
    lastSpoken.current = last.id;
    if (readAloud) speech.speak(messageText(last), language);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [last?.id, readAloud, language]);

  useEffect(() => {
    if (!readAloud) speech.stop();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [readAloud]);

  const busy = session.busy === 'processing' || transcribing;
  const avatarState: AvatarState = recorder.state === 'recording' ? 'listening' : busy ? 'processing' : speech.speaking ? 'speaking' : 'idle';

  const working = transcribing ? t('chat.transcribing') : session.busy === 'processing' ? t('chat.processing') : session.busy === 'translating' ? t('chat.translating') : null;
  const shown = notice ?? (session.error ? { key: `error.${session.error}` } : null);
  const dismissError = () => {
    setNotice(null);
    session.clearError();
  };

  // While a number is being asked for, the message box takes the answer; anything else is a chat message.
  const question = session.question;
  const send = (text: string) => {
    setNotice(null);
    if (question?.kind === 'number' && /^[\d,.\s]+$/.test(text)) {
      const n = Math.round(Number(text.replace(/[,\s]/g, '')));
      const min = question.min ?? 0;
      const max = question.max ?? Number.MAX_SAFE_INTEGER;
      if (!Number.isFinite(n) || n < min || n > max) {
        setNotice({ key: 'chat.number_invalid', params: { min: formatNumber(min), max: formatNumber(max) } });
        return;
      }
      session.answer(question.field, n);
      return;
    }
    session.sendText(text);
  };
  const hintKey = question ? `q.${question.field}.hint` : '';
  const numeric = question?.kind === 'number' ? { hint: t(hintKey) === hintKey ? null : t(hintKey) } : null;

  const restartControl = confirmRestart ? (
    <div className="flex flex-wrap items-center justify-end gap-2 text-sm">
      <span className="text-ink-muted">{t('chat.restart_confirm')}</span>
      <button type="button" className="btn-secondary min-h-[40px] px-3" onClick={() => setConfirmRestart(false)}>
        {t('common.cancel')}
      </button>
      <button
        type="button"
        className="btn-primary min-h-[40px] px-3"
        onClick={() => {
          speech.stop();
          session.restart();
          lastSpoken.current = null;
          setConfirmRestart(false);
        }}
      >
        {t('common.confirm')}
      </button>
    </div>
  ) : (
    <button type="button" className="btn-quiet min-h-[40px] text-sm" onClick={() => setConfirmRestart(true)}>
      <RotateCcw aria-hidden className="h-4 w-4" />
      {t('chat.restart')}
    </button>
  );

  return (
    <main id="main" className="min-h-0 flex-1">
      {/*
        Grid: the figure always occupies the bottom-left cell, so it can never overlap messages or controls.
        Small screens: messages and controls span the width and the figure sits in the last row.
        From md up: the figure takes the full-height left column, anchored to the bottom.
      */}
      <div
        id="chat-root"
        className="mx-auto grid h-full min-h-0 w-full max-w-6xl grid-cols-[72px_1fr] grid-rows-[auto_minmax(0,1fr)_auto_auto] gap-x-3 px-3 sm:px-6 md:grid-cols-[132px_1fr] md:grid-rows-[auto_minmax(0,1fr)_auto] lg:grid-cols-[232px_1fr]"
      >
        <div className="col-span-2 flex justify-end md:col-span-1 md:col-start-2">{restartControl}</div>

        <div className="col-span-2 flex min-h-0 flex-col md:col-span-1 md:col-start-2 md:row-start-2">
          <MessageList messages={session.messages} working={working} />
        </div>

        <div className="col-span-2 space-y-3 pb-3 md:col-span-1 md:col-start-2 md:row-start-3">
          {shown && (
            <div role="alert" className="flex items-start justify-between gap-3 rounded border border-bad/30 bg-bad-soft px-4 py-3 text-bad">
              <p>{t(shown.key, shown.params)}</p>
              <button type="button" onClick={dismissError} aria-label={t('common.cancel')} className="-m-2 flex min-h-tap min-w-tap items-center justify-center">
                <X aria-hidden className="h-5 w-5" />
              </button>
            </div>
          )}

          {session.ready && (
            <div className="flex flex-wrap items-center gap-x-4 gap-y-2 rounded border border-brand/20 bg-brand-soft px-3 py-2">
              <p className="hidden flex-1 text-sm text-ink-muted sm:block">{session.question ? t('chat.keep_answering') : t('chat.all_done')}</p>
              <Link href="/schemes" className="btn-primary w-full sm:w-auto">
                {t('chat.view_results')}
                <ArrowRight aria-hidden className="h-5 w-5" />
              </Link>
            </div>
          )}

          {session.question && (
            <AnswerPanel
              question={session.question}
              disabled={busy || recorder.state === 'recording'}
              onAnswer={(v) => session.answer(session.question!.field, v)}
              onSkip={() => session.answer(session.question!.field, null)}
            />
          )}

          <Composer
            numeric={numeric}
            disabled={busy}
            recording={recorder.state === 'recording'}
            readAloud={readAloud}
            onSend={send}
            onToggleRecording={() => (recorder.state === 'recording' ? recorder.stop() : recorder.start())}
            onToggleReadAloud={() => setReadAloud((v) => !v)}
          />
        </div>

        <aside className="row-start-4 flex flex-col justify-end self-end md:col-start-1 md:row-span-3 md:row-start-1">
          <div className="relative h-[84px] overflow-hidden md:h-auto md:overflow-visible">
            <Avatar state={avatarState} level={speech.level} className="w-full" />
          </div>
        </aside>
        <p className="row-start-4 self-center text-sm text-ink-muted md:hidden" aria-hidden>
          {t(`avatar.${avatarState}`)}
        </p>
      </div>
    </main>
  );
}
