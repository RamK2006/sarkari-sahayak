import type {
  AnalyzeResponse,
  ChatResponse,
  EligibilityResponse,
  GuidePlan,
  IntakeState,
  Profile,
  SchemeDetailResponse,
  SearchResponse,
} from './types';

interface MetaResponse {
  scheme_count: number;
}

/** Errors carry a stable code; components render the localized message for it. */
export class ApiError extends Error {
  constructor(public code: string, public status = 0) {
    super(code);
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let res: Response;
  try {
    res = await fetch(`/api${path}`, init);
  } catch {
    throw new ApiError('network');
  }
  if (!res.ok) {
    let code = 'generic';
    try {
      code = (await res.json())?.detail?.code ?? code;
    } catch {
      /* non-JSON error body */
    }
    throw new ApiError(code, res.status);
  }
  return res.json() as Promise<T>;
}

const post = <T>(path: string, body: unknown) =>
  request<T>(path, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) });

export interface VaultRef {
  id: string;
  doc_type: string;
  expiry_date: string | null;
}

export interface Citizen {
  language: string;
  profile: Profile;
  skipped: string[];
  vault: VaultRef[];
}

export const api = {
  meta: () => request<MetaResponse>('/meta'),

  intakeState: (c: Citizen) => post<IntakeState>('/intake/state', c),
  answer: (c: Citizen, field: string, value: string | number | boolean | null) =>
    post<IntakeState>('/intake/answer', { ...c, field, value }),

  chat: (c: Citizen, message: string, history: { role: string; content: string }[]) =>
    post<ChatResponse>('/chat', { ...c, message, history }),

  eligibility: (c: Citizen) => post<EligibilityResponse>('/eligibility', c),
  scheme: (id: string, c: Citizen) => post<SchemeDetailResponse>(`/schemes/${encodeURIComponent(id)}`, c),
  search: (body: { language: string; query: string; state: string | null; filters: Profile; limit?: number }) =>
    post<SearchResponse>('/search/schemes', body),
  states: (lang: string) =>
    request<{ states: { value: string; label: string }[]; translated: boolean }>(`/states?lang=${encodeURIComponent(lang)}`),

  translate: (language: string, texts: string[], source: 'en' | 'auto' = 'auto') =>
    post<{ texts: string[]; ok: boolean[] }>('/translate', { language, texts, source }),

  async transcribe(audio: Blob, language: string): Promise<string> {
    const form = new FormData();
    form.append('audio', audio, 'recording');
    form.append('language', language);
    return (await request<{ transcript: string }>('/voice/stt', { method: 'POST', body: form })).transcript;
  },

  async speak(text: string, language: string): Promise<Blob> {
    let res: Response;
    try {
      res = await fetch('/api/voice/tts', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text, language }),
      });
    } catch {
      throw new ApiError('network');
    }
    if (!res.ok) {
      let code = 'service_unavailable';
      try {
        code = (await res.json())?.detail?.code ?? code;
      } catch {
        /* ignore */
      }
      throw new ApiError(code, res.status);
    }
    return res.blob();
  },

  analyzeDocument(file: File) {
    const form = new FormData();
    form.append('file', file, file.name);
    return request<AnalyzeResponse>('/documents/analyze', { method: 'POST', body: form });
  },

  guidePlan: (body: { language: string; goal: string; scheme_id: string | null; citizen_data: Record<string, unknown> }) =>
    post<GuidePlan>('/guide/plan', body),
  guideClassify: (language: string, text: string) => post<{ intent: string }>('/guide/classify', { language, text }),
};
