'use client';

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from 'react';
import { api, ApiError } from './api';
import { useI18n } from './i18n';
import type { IntakeState, Message, Profile, Question } from './types';

const STORAGE_KEY = 'sa.session.v1';

interface Persisted {
  profile: Profile;
  skipped: string[];
  messages: Message[];
  question: Question | null;
  ready: boolean;
}

const EMPTY: Persisted = { profile: {}, skipped: [], messages: [], question: null, ready: false };

export type Busy = 'idle' | 'processing' | 'translating';

interface SessionApi extends Persisted {
  hydrated: boolean;
  busy: Busy;
  error: string | null;
  answer: (field: string, value: string | number | boolean | null) => Promise<void>;
  sendText: (text: string) => Promise<void>;
  askAgain: (field: string) => Promise<void>;
  restart: () => void;
  clearError: () => void;
  /** Citizen payload for API calls that evaluate eligibility. */
  citizen: { language: string; profile: Profile; skipped: string[] };
}

const Ctx = createContext<SessionApi | null>(null);

let counter = 0;
const nextId = () => `m${Date.now().toString(36)}${(counter++).toString(36)}`;

const errorCode = (e: unknown) => (e instanceof ApiError ? e.code : 'generic');

export function SessionProvider({ children }: { children: ReactNode }) {
  const { language } = useI18n();
  const [state, setState] = useState<Persisted>(EMPTY);
  const [hydrated, setHydrated] = useState(false);
  const [busy, setBusy] = useState<Busy>('idle');
  const [error, setError] = useState<string | null>(null);
  const stateRef = useRef(state);
  stateRef.current = state;
  const seeding = useRef(false);

  // Restore from this browser; nothing is stored on the server.
  useEffect(() => {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      if (raw) setState({ ...EMPTY, ...(JSON.parse(raw) as Persisted) });
    } catch {
      /* corrupt or unavailable storage: start fresh */
    }
    setHydrated(true);
  }, []);

  useEffect(() => {
    if (!hydrated) return;
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
    } catch {
      /* storage full or unavailable */
    }
  }, [state, hydrated]);

  const citizen = useMemo(
    () => ({ language, profile: state.profile, skipped: state.skipped }),
    [language, state.profile, state.skipped],
  );

  const apply = useCallback((res: IntakeState, extra: Message[] = []) => {
    setState((s) => {
      const messages = [...s.messages, ...extra];
      return { ...s, profile: res.profile, skipped: res.skipped, question: res.next_question, ready: res.ready, messages };
    });
  }, []);

  /** Messages the assistant adds after the state changes: the next question, or completion. */
  const followUp = useCallback((res: IntakeState, before: Persisted): Message[] => {
    if (res.next_question) {
      return [{ id: nextId(), role: 'assistant', kind: 'question', field: res.next_question.field }];
    }
    const alreadyDone = before.messages.some((m) => m.kind === 'all_done');
    return res.ready && !alreadyDone ? [{ id: nextId(), role: 'assistant', kind: 'all_done' }] : [];
  }, []);

  // Greeting and the first question for a new (or restarted) conversation.
  const empty = state.messages.length === 0;
  useEffect(() => {
    if (!hydrated || !empty || seeding.current) return;
    seeding.current = true;
    api
      .intakeState({ language, profile: {}, skipped: [] })
      .then((res) => {
        apply(res, [
          { id: nextId(), role: 'assistant', kind: 'greeting' },
          ...followUp(res, EMPTY),
        ]);
      })
      .catch((e) => setError(errorCode(e)))
      .finally(() => {
        seeding.current = false;
      });
  }, [hydrated, empty, language, apply, followUp]);

  const answer = useCallback<SessionApi['answer']>(
    async (field, value) => {
      setError(null);
      setBusy('processing');
      const before = stateRef.current;
      try {
        const res = await api.answer({ language, profile: before.profile, skipped: before.skipped }, field, value);
        apply(res, [{ id: nextId(), role: 'user', kind: 'answer', field, value }, ...followUp(res, before)]);
      } catch (e) {
        setError(errorCode(e));
      } finally {
        setBusy('idle');
      }
    },
    [language, apply, followUp],
  );

  const sendText = useCallback<SessionApi['sendText']>(
    async (text) => {
      setError(null);
      setBusy('processing');
      const before = stateRef.current;
      const history = before.messages
        .filter((m) => m.kind === 'text')
        .map((m) => ({ role: m.role, content: (m as { text: string }).text }));
      const userMsg: Message = { id: nextId(), role: 'user', kind: 'text', text };
      setState((s) => ({ ...s, messages: [...s.messages, userMsg] }));
      try {
        const res = await api.chat({ language, profile: before.profile, skipped: before.skipped }, text, history, before.question?.field ?? null);
        const out: Message[] = [];
        if (res.reply) out.push({ id: nextId(), role: 'assistant', kind: 'text', text: res.reply, lang: language });
        const changed = Object.keys(res.applied).length > 0;
        if (!res.reply && !changed) out.push({ id: nextId(), role: 'assistant', kind: 'error', code: 'generic' });
        // Ask the next question again after a free-text reply so the conversation ends on it.
        if (res.reply || changed) out.push(...followUp(res, before));
        apply(res, out);
      } catch (e) {
        setError(errorCode(e));
      } finally {
        setBusy('idle');
      }
    },
    [language, apply, followUp],
  );

  const askAgain = useCallback<SessionApi['askAgain']>(
    async (field) => {
      setError(null);
      try {
        const question = await api.question(field);
        setState((s) => ({
          ...s,
          question,
          messages: [...s.messages, { id: nextId(), role: 'assistant', kind: 'question', field }],
        }));
      } catch (e) {
        setError(errorCode(e));
      }
    },
    [],
  );

  const restart = useCallback(() => {
    setState(EMPTY);
    setError(null);
  }, []);

  // When the language changes, translate free-text replies from the model so nothing stays stale.
  // Questions, greetings and results are rendered from locale files and update instantly.
  useEffect(() => {
    if (!hydrated) return;
    const stale = stateRef.current.messages.filter((m) => m.kind === 'text' && m.role === 'assistant' && m.lang !== language);
    if (stale.length === 0) return;
    let cancelled = false;
    setBusy('translating');
    api
      .translate(language, stale.map((m) => (m as { text: string }).text))
      .then(({ texts }) => {
        if (cancelled) return;
        const byId = new Map(stale.map((m, i) => [m.id, texts[i]]));
        setState((s) => ({
          ...s,
          messages: s.messages.map((m) =>
            byId.has(m.id) && m.kind === 'text' ? { ...m, text: byId.get(m.id)!, lang: language } : m,
          ),
        }));
      })
      .catch((e) => !cancelled && setError(errorCode(e)))
      .finally(() => !cancelled && setBusy('idle'));
    return () => {
      cancelled = true;
    };
  }, [language, hydrated]);

  const value: SessionApi = {
    ...state,
    hydrated,
    busy,
    error,
    answer,
    sendText,
    askAgain,
    restart,
    clearError: () => setError(null),
    citizen,
  };
  return <Ctx.Provider value={value}>{children}</Ctx.Provider>;
}

export function useSession(): SessionApi {
  const ctx = useContext(Ctx);
  if (!ctx) throw new Error('useSession must be used inside SessionProvider');
  return ctx;
}
