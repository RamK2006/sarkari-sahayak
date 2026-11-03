import type {
  ChatResponse,
  EligibilityResponse,
  IntakeState,
  MetaResponse,
  Profile,
  Question,
  SchemeDetailResponse,
} from './types';

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
      const body = await res.json();
      code = body?.detail?.code ?? code;
    } catch {
      /* non-JSON error body */
    }
    throw new ApiError(code, res.status);
  }
  return res.json() as Promise<T>;
}

const post = <T>(path: string, body: unknown) =>
  request<T>(path, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });

interface Citizen {
  language: string;
  profile: Profile;
  skipped: string[];
}

export const api = {
  meta: () => request<MetaResponse>('/meta'),

  question: (field: string) => request<Question>(`/intake/question/${encodeURIComponent(field)}`),

  intakeState: (c: Citizen) => post<IntakeState>('/intake/state', c),

  answer: (c: Citizen, field: string, value: string | number | boolean | null) =>
    post<IntakeState>('/intake/answer', { ...c, field, value }),

  chat: (c: Citizen, message: string, history: { role: string; content: string }[], asking: string | null) =>
    post<ChatResponse>('/chat', { ...c, message, history, asking }),

  eligibility: (c: Citizen) => post<EligibilityResponse>('/eligibility', c),

  scheme: (id: string, c: Citizen) => post<SchemeDetailResponse>(`/schemes/${encodeURIComponent(id)}`, c),

  translate: (language: string, texts: string[]) =>
    post<{ texts: string[] }>('/translate', { language, texts }),

  async transcribe(audio: Blob, language: string): Promise<string> {
    const form = new FormData();
    form.append('audio', audio, 'recording');
    form.append('language', language);
    const out = await request<{ transcript: string }>('/voice/stt', { method: 'POST', body: form });
    return out.transcript;
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
    if (!res.ok) throw new ApiError('service_unavailable', res.status);
    return res.blob();
  },
};
