'use client';

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from 'react';
import en from '@/locales/en.json';
import { DEFAULT_LANGUAGE, isSupported } from './languages';

type Messages = Record<string, string>;
export type Params = Record<string, string | number>;

const STORAGE_KEY = 'sa.language';

const loaders: Record<string, () => Promise<{ default: Messages }>> = {
  hi: () => import('@/locales/hi.json'),
  bn: () => import('@/locales/bn.json'),
  te: () => import('@/locales/te.json'),
  mr: () => import('@/locales/mr.json'),
  ta: () => import('@/locales/ta.json'),
  gu: () => import('@/locales/gu.json'),
  kn: () => import('@/locales/kn.json'),
  ml: () => import('@/locales/ml.json'),
  pa: () => import('@/locales/pa.json'),
  od: () => import('@/locales/od.json'),
};

async function load(language: string): Promise<Messages> {
  if (language === 'en') return en as Messages;
  return (await loaders[language]()).default;
}

interface I18n {
  language: string;
  setLanguage: (code: string) => void;
  /** True once the user has explicitly chosen a language. */
  chosen: boolean;
  t: (key: string, params?: Params) => string;
  formatNumber: (n: number) => string;
}

const Ctx = createContext<I18n | null>(null);

export function I18nProvider({ children }: { children: ReactNode }) {
  const [language, setLang] = useState(DEFAULT_LANGUAGE);
  const [messages, setMessages] = useState<Messages>(en as Messages);
  const [chosen, setChosen] = useState(false);
  const [ready, setReady] = useState(false);

  // Restore the saved language once on mount.
  useEffect(() => {
    let saved: string | null = null;
    try {
      saved = localStorage.getItem(STORAGE_KEY);
    } catch {
      /* storage unavailable */
    }
    if (isSupported(saved)) {
      setChosen(true);
      setLang(saved);
    } else {
      setReady(true);
    }
  }, []);

  useEffect(() => {
    let cancelled = false;
    load(language).then((m) => {
      if (cancelled) return;
      setMessages(m);
      setReady(true);
      document.documentElement.lang = language;
    });
    return () => {
      cancelled = true;
    };
  }, [language]);

  const setLanguage = useCallback((code: string) => {
    if (!isSupported(code)) return;
    setLang(code);
    setChosen(true);
    try {
      localStorage.setItem(STORAGE_KEY, code);
    } catch {
      /* storage unavailable */
    }
  }, []);

  const t = useCallback(
    (key: string, params?: Params) => {
      const template = messages[key] ?? (en as Messages)[key] ?? key;
      if (!params) return template;
      return template.replace(/\{(\w+)\}/g, (_, name) => String(params[name] ?? `{${name}}`));
    },
    [messages],
  );

  const formatNumber = useCallback(
    (n: number) => new Intl.NumberFormat(`${language}-IN`).format(n),
    [language],
  );

  const value = useMemo(
    () => ({ language, setLanguage, chosen, t, formatNumber }),
    [language, setLanguage, chosen, t, formatNumber],
  );

  // Avoid a flash of the wrong language while the saved locale loads.
  return (
    <Ctx.Provider value={value}>
      <div style={{ visibility: ready ? 'visible' : 'hidden' }}>{children}</div>
    </Ctx.Provider>
  );
}

export function useI18n(): I18n {
  const ctx = useContext(Ctx);
  if (!ctx) throw new Error('useI18n must be used inside I18nProvider');
  return ctx;
}
