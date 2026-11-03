'use client';

import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState, type ReactNode } from 'react';
import { api, ApiError, type Citizen } from './api';
import { useI18n } from './i18n';
import type { ChatResponse, Gesture, Message, Mood, Profile } from './types';
import { useVault } from './vault';

const STORAGE_KEY = 'sa.session.v2';

interface Persisted {
  profile: Profile;
  skipped: string[];
  messages: Message[];
}
const EMPTY: Persisted = { profile: {}, skipped: [], messages: [] };

export type Busy = 'idle' | 'processing' | 'translating';

interface SessionApi extends Persisted {
  hydrated: boolean;
  busy: Busy;
  error: string | null;
  /** Latest emotion and gesture requested by the assistant; consumed by the avatar. */
  mood: Mood;
  gesture: { value: Gesture; key: number };
  /** Send a message (typed or transcribed). Resolves with the response so voice mode can speak it. */
  send: (text: string) => Promise<ChatResponse | null>;
  /** Save a structured answer from the quick check or a document. */
  setFacts: (facts: Profile, skippedFields?: string[]) => void;
  answer: (field: string, value: string | number | boolean | null) => Promise<void>;
  restart: () => void;
  clearError: () => void;
  citizen: Citizen;
}

const Ctx = createContext<SessionApi | null>(null);

let counter = 0;
const nextId = () => `m${Date.now().toString(36)}${(counter++).toString(36)}`;
const errorCode = (e: unknown) => (e instanceof ApiError ? e.code : 'generic');

export function SessionProvider({ children }: { children: ReactNode }) {
  const { language } = useI18n();
  const vault = useVault();
  const [state, setState] = useState<Persisted>(EMPTY);
  const [hydrated, setHydrated] = useState(false);
  const [busy, setBusy] = useState<Busy>('idle');
  const [error, setError] = useState<string | null>(null);
  const [mood, setMood] = useState<Mood>('neutral');
  const [gesture, setGesture] = useState<{ value: Gesture; key: number }>({ value: 'none', key: 0 });
  const ref = useRef(state);
  ref.current = state;

  useEffect(() => {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      if (raw) setState({ ...EMPTY, ...(JSON.parse(raw) as Persisted) });
    } catch {
      /* start fresh */
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

  const citizen = useMemo<Citizen>(
    () => ({ language, profile: state.profile, skipped: state.skipped, vault: vault.refs }),
    [language, state.profile, state.skipped, vault.refs],
  );
  const citizenRef = useRef(citizen);
  citizenRef.current = citizen;

  const send = useCallback<SessionApi['send']>(async (text) => {
    setError(null);
    setBusy('processing');
    setMood('thinking');
    const before = ref.current;
    const history = before.messages
      .filter((m) => m.kind === 'text')
      .map((m) => ({ role: m.role, content: (m as { text: string }).text }));
    setState((s) => ({ ...s, messages: [...s.messages, { id: nextId(), role: 'user', kind: 'text', text }] }));
    try {
      const res = await api.chat(citizenRef.current, text, history);
      setState((s) => ({
        ...s,
        profile: res.profile,
        skipped: res.skipped,
        messages: [
          ...s.messages,
          { id: nextId(), role: 'assistant', kind: 'text', text: res.reply, lang: citizenRef.current.language, mood: res.mood, schemes: res.schemes.map((c) => c.scheme.id), guide: res.guide, upload: res.upload },
        ],
      }));
      setMood(res.mood);
      setGesture((g) => ({ value: res.gesture, key: g.key + 1 }));
      return res;
    } catch (e) {
      setMood('empathetic');
      setError(errorCode(e));
      return null;
    } finally {
      setBusy('idle');
    }
  }, []);

  const setFacts = useCallback<SessionApi['setFacts']>((facts, skippedFields = []) => {
    setState((s) => ({
      ...s,
      profile: { ...s.profile, ...facts },
      skipped: [...new Set([...s.skipped.filter((f) => !(f in facts)), ...skippedFields])],
    }));
  }, []);

  const answer = useCallback<SessionApi['answer']>(async (field, value) => {
    setError(null);
    try {
      const res = await api.answer(citizenRef.current, field, value);
      setState((s) => ({ ...s, profile: res.profile, skipped: res.skipped }));
    } catch (e) {
      setError(errorCode(e));
    }
  }, []);

  const restart = useCallback(() => {
    setState(EMPTY);
    setError(null);
    setMood('neutral');
  }, []);

  // A language switch translates earlier replies so nothing stays stale; the interface itself updates instantly.
  useEffect(() => {
    if (!hydrated) return;
    const stale = ref.current.messages.filter((m) => m.kind === 'text' && m.role === 'assistant' && m.lang !== language);
    if (stale.length === 0) return;
    let cancelled = false;
    setBusy('translating');
    api
      .translate(language, stale.map((m) => (m as { text: string }).text))
      .then(({ texts, ok }) => {
        if (cancelled) return;
        const byId = new Map(stale.flatMap((m, i) => (ok[i] ? [[m.id, texts[i]] as [string, string]] : [])));
        setState((s) => ({
          ...s,
          messages: s.messages.map((m) => (byId.has(m.id) && m.kind === 'text' ? { ...m, text: byId.get(m.id)!, lang: language } : m)),
        }));
      })
      .catch((e) => !cancelled && setError(errorCode(e)))
      .finally(() => !cancelled && setBusy('idle'));
    return () => {
      cancelled = true;
    };
  }, [language, hydrated]);

  const value: SessionApi = {
    ...state, hydrated, busy, error, mood, gesture, send, setFacts, answer, restart,
    clearError: () => setError(null), citizen,
  };
  return <Ctx.Provider value={value}>{children}</Ctx.Provider>;
}

export function useSession(): SessionApi {
  const ctx = useContext(Ctx);
  if (!ctx) throw new Error('useSession must be used inside SessionProvider');
  return ctx;
}
