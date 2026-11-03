'use client';

import { useCallback, useEffect, useRef, useState, type FormEvent } from 'react';
import { Keyboard, Phone, PhoneOff, RotateCcw, Send, X } from 'lucide-react';
import { Avatar, type AvatarState } from '@/components/Avatar';
import { Conversation } from '@/components/talk/Conversation';
import { useSpeech } from '@/hooks/useSpeech';
import { useVoiceLoop, voiceSupported } from '@/hooks/useVoiceLoop';
import { api, ApiError } from '@/lib/api';
import { useI18n, type Params } from '@/lib/i18n';
import { hasSpeech } from '@/lib/languages';
import type { Gesture } from '@/lib/types';
import { useSession } from '@/lib/session';

type Mode = 'call' | 'chat';
type Notice = { key: string; params?: Params } | null;

export default function TalkPage() {
  const { t, language } = useI18n();
  const session = useSession();

  const [mode, setMode] = useState<Mode>('call');
  const [notice, setNotice] = useState<Notice>(null);
  const [text, setText] = useState('');
  const [confirmRestart, setConfirmRestart] = useState(false);
  const [canVoice, setCanVoice] = useState(true); // decided on the client; server and first render agree
  const [gesture, setGesture] = useState<{ value: Gesture; key: number }>({ value: 'none', key: 0 });

  const languageRef = useRef(language);
  languageRef.current = language;

  useEffect(() => {
    setCanVoice(voiceSupported());
    try {
      if (localStorage.getItem('sa.mode') === 'chat') setMode('chat');
    } catch {
      /* default to call */
    }
  }, []);

  // Greet with the regional gesture whenever the language is set or changed; follow the assistant's gestures after that.
  useEffect(() => setGesture({ value: 'namaste', key: Date.now() }), [language]);
  useEffect(() => {
    if (session.gesture.key > 0) setGesture(session.gesture);
  }, [session.gesture]);

  const speech = useSpeech(useCallback(() => setNotice({ key: 'chat.speak_failed' }), []));

  const loop = useVoiceLoop({
    onUtterance: async (audio) => {
      try {
        const transcript = await api.transcribe(audio, languageRef.current);
        if (!transcript) {
          setNotice({ key: 'chat.no_speech' });
          return;
        }
        const res = await session.send(transcript);
        if (res?.reply) {
          if (!hasSpeech(languageRef.current)) {
            setNotice({ key: 'talk.tts_unavailable' });
            return;
          }
          loop.setPhase('speaking');
          await speech.speak(res.reply, languageRef.current);
          if (loop.phaseRef.current === 'speaking') loop.setPhase('listening');
        }
      } catch (e) {
        setNotice({ key: `error.${e instanceof ApiError ? e.code : 'generic'}` });
      }
    },
    onBargeIn: () => speech.stop(),
    onError: (code) => setNotice({ key: code === 'mic_denied' ? 'chat.mic_denied' : 'chat.mic_unsupported' }),
  });

  const startCall = async () => {
    setNotice(null);
    await loop.start();
    if (hasSpeech(language)) {
      loop.setPhase('speaking');
      await speech.speak(t('talk.call_welcome'), language);
      if (loop.phaseRef.current === 'speaking') loop.setPhase('listening');
    } else setNotice({ key: 'talk.tts_unavailable' });
  };
  const endCall = () => {
    speech.stop();
    loop.stop();
  };

  const switchMode = (next: Mode) => {
    if (next === 'chat') endCall();
    setMode(next);
    try {
      localStorage.setItem('sa.mode', next);
    } catch {
      /* ignore */
    }
  };

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    const value = text.trim();
    if (!value || session.busy === 'processing') return;
    setText('');
    setNotice(null);
    await session.send(value);
  };

  const inCall = loop.phase !== 'off';
  const avatarState: AvatarState =
    loop.phase === 'capturing' || loop.phase === 'listening'
      ? 'listening'
      : loop.phase === 'processing' || session.busy === 'processing'
        ? 'processing'
        : speech.speaking
          ? 'speaking'
          : 'idle';

  const working =
    session.busy === 'processing' ? t('chat.processing') : session.busy === 'translating' ? t('chat.translating') : null;
  const shown = notice ?? (session.error ? { key: `error.${session.error}` } : null);
  const phaseText: Record<string, string> = {
    listening: t('talk.listening'),
    capturing: t('talk.capturing'),
    processing: t('talk.processing'),
    speaking: t('talk.speaking'),
  };

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
          endCall();
          session.restart();
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
      <div
        id="chat-root"
        className="mx-auto grid h-full min-h-0 w-full max-w-6xl grid-cols-[84px_1fr] grid-rows-[auto_minmax(0,1fr)_auto_auto] gap-x-3 px-3 sm:px-6 md:grid-cols-[150px_1fr] md:grid-rows-[auto_minmax(0,1fr)_auto] lg:grid-cols-[260px_1fr]"
      >
        <div className="col-span-2 flex flex-wrap items-center justify-between gap-2 md:col-span-1 md:col-start-2">
          <div role="radiogroup" aria-label={t('talk.mode_label')} className="flex rounded border border-line-strong bg-surface p-0.5">
            {(['call', 'chat'] as Mode[]).map((m) => (
              <button
                key={m}
                type="button"
                role="radio"
                aria-checked={mode === m}
                onClick={() => switchMode(m)}
                className={`flex min-h-[40px] items-center gap-2 rounded px-3 text-sm font-medium ${mode === m ? 'bg-brand text-onbrand' : 'text-ink-muted hover:text-ink'}`}
              >
                {m === 'call' ? <Phone aria-hidden className="h-4 w-4" /> : <Keyboard aria-hidden className="h-4 w-4" />}
                {t(m === 'call' ? 'talk.mode_call' : 'talk.mode_chat')}
              </button>
            ))}
          </div>
          {restartControl}
        </div>

        <div className="col-span-2 flex min-h-0 flex-col md:col-span-1 md:col-start-2 md:row-start-2">
          <Conversation messages={session.messages} working={working} />
        </div>

        <div className="col-span-2 space-y-3 pb-3 md:col-span-1 md:col-start-2 md:row-start-3">
          {shown && (
            <div role="alert" className="flex items-start justify-between gap-3 rounded border border-bad/30 bg-bad-soft px-4 py-3 text-bad">
              <p>{t(shown.key, shown.params)}</p>
              <button
                type="button"
                onClick={() => {
                  setNotice(null);
                  session.clearError();
                }}
                aria-label={t('common.cancel')}
                className="-m-2 flex min-h-tap min-w-tap items-center justify-center"
              >
                <X aria-hidden className="h-5 w-5" />
              </button>
            </div>
          )}

          {mode === 'call' ? (
            <div className="flex flex-wrap items-center gap-3 border-t border-line pt-3">
              {inCall ? (
                <button type="button" onClick={endCall} className="btn border-bad bg-bad text-onbrand hover:opacity-90">
                  <PhoneOff aria-hidden className="h-5 w-5" />
                  {t('talk.call_end')}
                </button>
              ) : canVoice ? (
                <button type="button" onClick={startCall} className="btn-primary text-lg">
                  <Phone aria-hidden className="h-5 w-5" />
                  {t('talk.call_start')}
                </button>
              ) : (
                <p className="text-ink-muted">{t('chat.mic_unsupported')}</p>
              )}
              <p className="flex-1 text-ink-muted" aria-live="polite">
                {inCall ? phaseText[loop.phase] : t('talk.call_hint')}
              </p>
              {inCall && (
                <span
                  aria-hidden
                  className={`h-3 w-3 rounded-full ${loop.phase === 'capturing' ? 'animate-pulse bg-bad' : loop.phase === 'listening' ? 'bg-ok' : 'bg-ink-faint'}`}
                />
              )}
            </div>
          ) : (
            <form onSubmit={submit} className="flex items-stretch gap-2 border-t border-line pt-3">
              <label className="min-w-0 flex-1">
                <span className="sr-only">{t('chat.input_label')}</span>
                <input
                  className="field"
                  value={text}
                  onChange={(e) => setText(e.target.value)}
                  placeholder={t('talk.input_placeholder')}
                  maxLength={1000}
                  autoComplete="off"
                  disabled={session.busy === 'processing'}
                />
              </label>
              <button type="submit" disabled={!text.trim() || session.busy === 'processing'} className="btn-primary min-w-tap px-0 sm:px-5" aria-label={t('chat.send')}>
                <Send aria-hidden className="h-5 w-5" />
                <span className="hidden sm:inline">{t('chat.send')}</span>
              </button>
            </form>
          )}
        </div>

        {/* The figure is always in the bottom-left cell, so it never overlaps messages or controls. */}
        <aside className="row-start-4 flex flex-col justify-end self-end md:col-start-1 md:row-span-3 md:row-start-1">
          <div className="relative h-[84px] overflow-hidden md:h-auto md:overflow-visible">
            <Avatar language={language} state={avatarState} mood={session.mood} gesture={gesture} level={speech.level} className="w-full" />
          </div>
        </aside>
        <p className="row-start-4 self-center text-sm text-ink-muted md:hidden" aria-hidden>
          {t(`avatar.${avatarState}`)}
        </p>
      </div>
    </main>
  );
}
