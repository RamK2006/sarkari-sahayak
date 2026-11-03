'use client';

import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from 'react';
import en from '@/locales/en.json';
import { api } from './api';
import { DEFAULT_LANGUAGE, RTL_LANGUAGES, isSupported } from './languages';

type Messages = Record<string, string>;
export type Params = Record<string, string | number>;

const STORAGE_KEY = 'sa.language';
const CACHE_PREFIX = 'sa.i18n.v1.';
const EN = en as Messages;

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
  as: () => import('@/locales/as.json'),
  ur: () => import('@/locales/ur.json'),
  ne: () => import('@/locales/ne.json'),
  kok: () => import('@/locales/kok.json'),
  mai: () => import('@/locales/mai.json'),
  doi: () => import('@/locales/doi.json'),
  sd: () => import('@/locales/sd.json'),
  ks: () => import('@/locales/ks.json'),
  sa: () => import('@/locales/sa.json'),
  sat: () => import('@/locales/sat.json'),
  mni: () => import('@/locales/mni.json'),
  brx: () => import('@/locales/brx.json'),
};

const placeholders = (s: string) => (s.match(/\{\w+\}/g) ?? []).sort().join(',');

function readCache(language: string): Messages {
  try {
    return JSON.parse(localStorage.getItem(CACHE_PREFIX + language) ?? '{}');
  } catch {
    return {};
  }
}

/**
 * Keys missing from a language's shipped file (new strings, or a language whose file has not been generated
 * yet) are translated by Sarvam on demand, then cached in this browser. Placeholders are protected as tokens.
 */
async function fillMissing(language: string, have: Messages): Promise<Messages> {
  const out = { ...have };
  const protect = (text: string) => {
    const names: string[] = [];
    const masked = text.replace(/\{(\w+)\}/g, (_, n) => `[[${names.push(n)}]]`);
    return { masked, names };
  };
  // Up to three passes: strings that fail (for example under a rate limit) are retried after a pause.
  for (let pass = 0; pass < 3; pass++) {
    const missing = Object.keys(EN).filter((k) => !out[k]);
    if (missing.length === 0) break;
    if (pass > 0) await new Promise((r) => setTimeout(r, 4000 * pass));
    for (let i = 0; i < missing.length; i += 40) {
      const keys = missing.slice(i, i + 40);
      const prepared = keys.map((k) => protect(EN[k]));
      try {
        const { texts, ok } = await api.translate(language, prepared.map((p) => p.masked), 'en');
        texts.forEach((text, j) => {
          if (!ok[j]) return;
          const restored = prepared[j].names.reduce((acc, n, idx) => acc.replace(`[[${idx + 1}]]`, `{${n}}`), text);
          if (placeholders(restored) === placeholders(EN[keys[j]])) out[keys[j]] = restored;
        });
      } catch {
        /* this chunk is retried on the next pass */
      }
    }
  }
  try {
    localStorage.setItem(CACHE_PREFIX + language, JSON.stringify(out));
  } catch {
    /* storage unavailable */
  }
  return out;
}

interface I18n {
  language: string;
  setLanguage: (code: string) => void;
  chosen: boolean;
  /** True while strings for the selected language are still being prepared. */
  preparing: boolean;
  t: (key: string, params?: Params) => string;
  formatNumber: (n: number) => string;
  formatDate: (iso: string) => string;
}

const Ctx = createContext<I18n | null>(null);

export function I18nProvider({ children }: { children: ReactNode }) {
  const [language, setLang] = useState(DEFAULT_LANGUAGE);
  const [messages, setMessages] = useState<Messages>(EN);
  const [chosen, setChosen] = useState(false);
  const [ready, setReady] = useState(false);
  const [preparing, setPreparing] = useState(false);

  useEffect(() => {
    let saved: string | null = null;
    try {
      saved = localStorage.getItem(STORAGE_KEY);
    } catch {
      /* storage unavailable */
    }
    if (isSupported(saved) && saved !== DEFAULT_LANGUAGE) {
      setChosen(true);
      setLang(saved);
    } else {
      setReady(true);
    }
  }, []);

  useEffect(() => {
    let cancelled = false;
    document.documentElement.lang = language;
    document.documentElement.dir = RTL_LANGUAGES.has(language) ? 'rtl' : 'ltr';
    if (language === 'en') {
      setMessages(EN);
      setReady(true);
      return;
    }
    (async () => {
      const shipped = (await loaders[language]()).default;
      const base = { ...readCache(language), ...shipped };
      if (cancelled) return;
      setMessages(base);
      setReady(true);
      if (Object.keys(EN).some((k) => !base[k])) {
        setPreparing(true);
        const filled = await fillMissing(language, base);
        if (!cancelled) setMessages(filled);
        if (!cancelled) setPreparing(false);
      }
    })();
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
      const template = messages[key] ?? EN[key] ?? key;
      if (!params) return template;
      return template.replace(/\{(\w+)\}/g, (_, name) => String(params[name] ?? `{${name}}`));
    },
    [messages],
  );

  const formatNumber = useCallback((n: number) => new Intl.NumberFormat(`${language}-IN`).format(n), [language]);
  const formatDate = useCallback(
    (iso: string) => {
      try {
        return new Intl.DateTimeFormat(`${language}-IN`, { dateStyle: 'long' }).format(new Date(`${iso}T00:00:00`));
      } catch {
        return iso;
      }
    },
    [language],
  );

  const value = useMemo(
    () => ({ language, setLanguage, chosen, preparing, t, formatNumber, formatDate }),
    [language, setLanguage, chosen, preparing, t, formatNumber, formatDate],
  );

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
