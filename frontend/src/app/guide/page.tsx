'use client';

import { Suspense, useCallback, useEffect, useMemo, useRef, useState, type FormEvent } from 'react';
import { useSearchParams } from 'next/navigation';
import { ArrowLeft, ArrowRight, Check, ExternalLink, Mic, MicOff, Volume2 } from 'lucide-react';
import { useSpeech } from '@/hooks/useSpeech';
import { useVoiceLoop, voiceSupported } from '@/hooks/useVoiceLoop';
import { api, ApiError } from '@/lib/api';
import { useI18n } from '@/lib/i18n';
import { hasSpeech } from '@/lib/languages';
import { useSession } from '@/lib/session';
import { useVault } from '@/lib/vault';
import type { GuidePlan } from '@/lib/types';

interface Item {
  step: number;
  field: number | null; // null: the step as a whole
}

function GuideInner() {
  const { t, language } = useI18n();
  const params = useSearchParams();
  const { profile } = useSession();
  const { guideData } = useVault();

  const [goal, setGoal] = useState(params.get('goal') ?? '');
  const schemeId = params.get('scheme');
  const [plan, setPlan] = useState<GuidePlan | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [pos, setPos] = useState(0);
  const [handsFree, setHandsFree] = useState(false);
  const [canVoice, setCanVoice] = useState(false);
  useEffect(() => setCanVoice(voiceSupported()), []);
  const languageRef = useRef(language);
  languageRef.current = language;

  const build = useCallback(
    async (g: string) => {
      setLoading(true);
      setError(null);
      setPos(0);
      try {
        setPlan(await api.guidePlan({ language, goal: g, scheme_id: schemeId, citizen_data: { documents: guideData, profile } }));
      } catch (e) {
        setError(e instanceof ApiError ? e.code : 'generic');
      } finally {
        setLoading(false);
      }
    },
    [language, schemeId, guideData, profile],
  );

  // A goal or scheme from the link starts the guide straight away; a language change rebuilds it in that language.
  useEffect(() => {
    if (schemeId || params.get('goal')) build(goal);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [language]);

  const items = useMemo<Item[]>(
    () => (plan ? plan.steps.flatMap((s, i): Item[] => (s.fields.length ? s.fields.map((_, j) => ({ step: i, field: j })) : [{ step: i, field: null }])) : []),
    [plan],
  );
  const item = items[pos];
  const done = plan && pos >= items.length;

  const speech = useSpeech(useCallback(() => setError('service_unavailable'), []));

  const spokenText = useCallback(
    (it: Item): string => {
      const s = plan!.steps[it.step];
      if (it.field === null) return `${s.title}. ${s.detail}`;
      const f = s.fields[it.field];
      return f.value ? t('guide.speak_with_value', { label: f.label, value: f.value, hint: f.hint }) : t('guide.speak_no_value', { label: f.label, hint: f.hint });
    },
    [plan, t],
  );

  const say = useCallback(
    async (it: Item | undefined) => {
      if (it && plan && hasSpeech(languageRef.current)) await speech.speak(spokenText(it), languageRef.current);
    },
    [plan, spokenText, speech],
  );

  const go = useCallback(
    (to: number) => {
      const n = Math.max(0, Math.min(items.length, to));
      setPos(n);
      if (handsFree) void say(items[n]);
    },
    [items, handsFree, say],
  );

  // Hands-free: the citizen answers aloud (done / repeat / back) after each spoken field.
  const posRef = useRef(pos);
  posRef.current = pos;
  const loop = useVoiceLoop({
    onUtterance: async (audio) => {
      const text = await api.transcribe(audio, languageRef.current).catch(() => '');
      if (!text) return;
      const { intent } = await api.guideClassify(languageRef.current, text).catch(() => ({ intent: 'repeat' }));
      const p = posRef.current;
      if (intent === 'confirm' || intent === 'skip') go(p + 1);
      else if (intent === 'back') go(p - 1);
      else void say(items[p]);
    },
    onBargeIn: () => speech.stop(),
    onError: () => setHandsFree(false),
  });

  const toggleHandsFree = async () => {
    if (handsFree) {
      loop.stop();
      setHandsFree(false);
      return;
    }
    setHandsFree(true);
    await loop.start();
    await say(item);
  };
  useEffect(() => () => loop.stop(), [loop]);

  const submit = (e: FormEvent) => {
    e.preventDefault();
    if (goal.trim()) build(goal.trim());
  };

  const step = plan && item ? plan.steps[item.step] : null;
  const field = step && item?.field !== null && item ? step.fields[item.field!] : null;

  return (
    <main id="main" className="mx-auto w-full max-w-3xl px-4 py-8 sm:px-6 sm:py-10">
      <h1 className="text-3xl">{plan?.title ?? t('guide.title')}</h1>

      {!schemeId && (
        <form onSubmit={submit} className="mt-6 flex flex-wrap items-end gap-3">
          <div className="min-w-[240px] flex-1">
            <label htmlFor="goal" className="mb-1 block font-medium">{t('guide.goal_label')}</label>
            <input id="goal" className="field" value={goal} onChange={(e) => setGoal(e.target.value)} placeholder={t('guide.goal_placeholder')} maxLength={300} />
          </div>
          <button type="submit" className="btn-primary" disabled={loading || !goal.trim()}>{t('guide.start')}</button>
        </form>
      )}

      {loading && <p role="status" className="mt-8 text-ink-muted">{t('guide.creating')}</p>}
      {error && <p role="alert" className="mt-6 rounded border border-bad/30 bg-bad-soft p-4 text-bad">{t(`error.${error}`)}</p>}

      {plan && !loading && (
        <>
          <p className="mt-4 text-sm text-ink-muted">{plan.grounded ? t('guide.grounded_note') : t('guide.general_note')}</p>

          {done ? (
            <section className="mt-8 border-y border-line py-8">
              <p className="font-display text-2xl">{t('guide.finished')}</p>
              <div className="mt-4 flex flex-wrap gap-3">
                <button type="button" className="btn-secondary" onClick={() => go(0)}>{t('guide.restart')}</button>
                {plan.apply_url && (
                  <a href={plan.apply_url} target="_blank" rel="noopener noreferrer" className="btn-primary">
                    {t('detail.open_website')}
                    <ExternalLink aria-hidden className="h-4 w-4" />
                  </a>
                )}
              </div>
            </section>
          ) : (
            step && (
              <section className="mt-6" aria-live="polite">
                <p className="text-sm font-medium text-ink-muted">{t('guide.step', { current: item.step + 1, total: plan.steps.length })}</p>
                <h2 className="mt-1 text-2xl">{step.title}</h2>
                <p className="mt-2 text-ink-muted">{step.detail}</p>

                {field && (
                  <div className="mt-6 rounded-lg border border-brand bg-brand-soft p-6">
                    <p className="text-sm font-medium text-ink-muted">{t('guide.field')}</p>
                    <p className="font-display text-2xl">{field.label}</p>
                    {field.value ? (
                      <p className="mt-3 text-lg"><span className="text-ink-muted">{t('guide.value_from_docs')}</span> <strong>{field.value}</strong></p>
                    ) : (
                      <p className="mt-3 text-ink-muted">{t('guide.no_value')}</p>
                    )}
                    {field.hint && <p className="mt-2">{field.hint}</p>}
                  </div>
                )}

                {step.fields.length > 1 && (
                  <ol className="mt-4 space-y-1 text-sm text-ink-muted">
                    {step.fields.map((f, j) => (
                      <li key={j} className={j === item.field ? 'font-semibold text-ink' : ''}>{f.label}</li>
                    ))}
                  </ol>
                )}

                <div className="mt-6 flex flex-wrap items-center gap-3">
                  <button type="button" className="btn-secondary" disabled={pos === 0} onClick={() => go(pos - 1)}>
                    <ArrowLeft aria-hidden className="h-5 w-5" />
                    {t('guide.prev')}
                  </button>
                  <button type="button" className="btn-primary" onClick={() => go(pos + 1)}>
                    <Check aria-hidden className="h-5 w-5" />
                    {field ? t('guide.confirm') : t('guide.next')}
                    <ArrowRight aria-hidden className="h-5 w-5" />
                  </button>
                  {hasSpeech(language) && (
                    <button type="button" className="btn-secondary" onClick={() => say(item)}>
                      <Volume2 aria-hidden className="h-5 w-5" />
                      {t('guide.read_aloud')}
                    </button>
                  )}
                </div>

                {hasSpeech(language) && canVoice && (
                  <div className="mt-6 border-t border-line pt-4">
                    <button type="button" aria-pressed={handsFree} onClick={toggleHandsFree} className="btn-secondary">
                      {handsFree ? <MicOff aria-hidden className="h-5 w-5" /> : <Mic aria-hidden className="h-5 w-5" />}
                      {t('guide.hands_free')}
                    </button>
                    <p className="mt-2 text-sm text-ink-muted">{t('guide.say_hint')}</p>
                  </div>
                )}
              </section>
            )
          )}
        </>
      )}
    </main>
  );
}

export default function GuidePage() {
  return (
    <Suspense fallback={null}>
      <GuideInner />
    </Suspense>
  );
}
