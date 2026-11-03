'use client';

import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from 'react';
import type { ReviewState, VaultDoc } from './types';

const KEY = 'sa.vault.v1';

// Mirrors the backend defaults (EXPIRING_SOON_DAYS / UPCOMING_DAYS) so reviews stay current without a request.
const SOON = 30;
const UPCOMING = 90;

export function reviewOf(expiry: string | null | undefined, today = new Date()): { state: ReviewState; days: number | null } {
  if (!expiry) return { state: 'no_expiry', days: null };
  const end = new Date(`${expiry}T00:00:00`);
  const start = new Date(today.getFullYear(), today.getMonth(), today.getDate());
  const days = Math.round((end.getTime() - start.getTime()) / 86_400_000);
  if (days < 0) return { state: 'expired', days };
  if (days <= SOON) return { state: 'expiring_soon', days };
  if (days <= UPCOMING) return { state: 'upcoming', days };
  return { state: 'valid', days };
}

interface VaultApi {
  docs: VaultDoc[];
  hydrated: boolean;
  add: (doc: VaultDoc) => void;
  update: (id: string, patch: Partial<VaultDoc>) => void;
  remove: (id: string) => void;
  /** Minimal references sent to the API (type and expiry only, no personal fields). */
  refs: { id: string; doc_type: string; expiry_date: string | null }[];
  /** Fields from the documents that the guide may copy into form fields. */
  guideData: Record<string, unknown>;
}

const Ctx = createContext<VaultApi | null>(null);

export function VaultProvider({ children }: { children: ReactNode }) {
  const [docs, setDocs] = useState<VaultDoc[]>([]);
  const [hydrated, setHydrated] = useState(false);

  useEffect(() => {
    try {
      const raw = localStorage.getItem(KEY);
      if (raw) setDocs(JSON.parse(raw));
    } catch {
      /* start empty */
    }
    setHydrated(true);
  }, []);

  useEffect(() => {
    if (!hydrated) return;
    try {
      localStorage.setItem(KEY, JSON.stringify(docs));
    } catch {
      /* storage full or unavailable */
    }
  }, [docs, hydrated]);

  const add = useCallback((doc: VaultDoc) => setDocs((d) => [doc, ...d]), []);
  const update = useCallback((id: string, patch: Partial<VaultDoc>) => setDocs((d) => d.map((x) => (x.id === id ? { ...x, ...patch } : x))), []);
  const remove = useCallback((id: string) => setDocs((d) => d.filter((x) => x.id !== id)), []);

  const refs = useMemo(() => docs.map((d) => ({ id: d.id, doc_type: d.doc_type, expiry_date: d.fields?.expiry_date ?? null })), [docs]);
  const guideData = useMemo(() => {
    const out: Record<string, unknown> = {};
    docs.forEach((d) => {
      if (d.fields) out[d.doc_type] = { holder_name: d.fields.holder_name, date_of_birth: d.fields.date_of_birth, issuer: d.fields.issuer, id_last4: d.fields.id_last4 };
    });
    return out;
  }, [docs]);

  const value = useMemo(() => ({ docs, hydrated, add, update, remove, refs, guideData }), [docs, hydrated, add, update, remove, refs, guideData]);
  return <Ctx.Provider value={value}>{children}</Ctx.Provider>;
}

export function useVault(): VaultApi {
  const ctx = useContext(Ctx);
  if (!ctx) throw new Error('useVault must be used inside VaultProvider');
  return ctx;
}
