export type Profile = Record<string, string | number | boolean>;

export type QuestionKind = 'number' | 'choice' | 'boolean';

export interface Question {
  field: string;
  kind: QuestionKind;
  skippable: boolean;
  options?: string[];
  min?: number;
  max?: number;
}

export interface IntakeState {
  profile: Profile;
  skipped: string[];
  next_question: Question | null;
  ready: boolean;
}

export interface ChatResponse extends IntakeState {
  reply: string;
  applied: Profile;
}

export type Outcome = 'met' | 'unmet' | 'unknown' | 'verify';
export type Status = 'eligible' | 'potentially_eligible' | 'insufficient_info' | 'not_eligible';

export interface CriterionItem {
  criterion: string;
  outcome: Outcome;
  params: Record<string, unknown>;
  field?: string;
  skipped?: boolean;
}

export interface Evaluation {
  scheme_id: string;
  status: Status;
  items: CriterionItem[];
  missing_fields: string[];
}

export interface SchemeBrief {
  id: string;
  name: string;
  ministry: string;
  summary: string;
  benefits: string;
  categories: string[];
  apply: { url: string | null; channel: string | null };
  source_url: string | null;
}

export interface SchemeDetail extends SchemeBrief {
  documents: string[];
  notes: string[];
  last_verified: string | null;
}

export interface EligibilityResponse {
  ready: boolean;
  translated: boolean;
  results: (Evaluation & { scheme: SchemeBrief })[];
}

export interface SchemeDetailResponse {
  scheme: SchemeDetail;
  evaluation: Evaluation;
  translated: boolean;
  ready: boolean;
}

export interface MetaResponse {
  scheme_count: number;
}

export type Message =
  | { id: string; role: 'assistant'; kind: 'greeting' }
  | { id: string; role: 'assistant'; kind: 'question'; field: string }
  | { id: string; role: 'assistant'; kind: 'text'; text: string; lang: string }
  | { id: string; role: 'assistant'; kind: 'all_done' }
  | { id: string; role: 'assistant'; kind: 'error'; code: string }
  | { id: string; role: 'user'; kind: 'answer'; field: string; value: string | number | boolean | null }
  | { id: string; role: 'user'; kind: 'text'; text: string };
