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

export type Outcome = 'met' | 'unmet' | 'unknown' | 'verify';
export type Status = 'eligible' | 'potentially_eligible' | 'insufficient_info' | 'not_assessed' | 'not_eligible';
export type Mood = 'neutral' | 'happy' | 'empathetic' | 'serious' | 'thinking';
export type Gesture = 'none' | 'namaste' | 'open' | 'point';

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

export type DocStatus = 'have' | 'expired' | 'missing' | 'unrecognised';

export interface SchemeDetailResponse {
  scheme: SchemeDetail;
  evaluation: Evaluation;
  document_status: { status: DocStatus; vault_id: string | null }[];
  translated: boolean;
  ready: boolean;
}

export interface SchemeCard {
  scheme: SchemeBrief;
  status: Status;
}

export interface SearchResponse {
  results: { scheme: SchemeBrief; status: Status; missing_fields: string[] }[];
  translated: boolean;
  total_catalog: number;
}

export interface ChatResponse {
  reply: string;
  mood: Mood;
  gesture: Gesture;
  guide: string | null;
  upload: string | null;
  applied: Profile;
  profile: Profile;
  skipped: string[];
  schemes: SchemeCard[];
  translated: boolean;
}

export type ReviewState = 'expired' | 'expiring_soon' | 'upcoming' | 'valid' | 'no_expiry';

export interface DocumentFields {
  doc_type: string;
  holder_name: string | null;
  date_of_birth: string | null;
  issue_date: string | null;
  expiry_date: string | null;
  issuer: string | null;
  id_last4: string | null;
  quality_issues: string[];
}

export interface AnalyzeResponse {
  doc_type: string;
  readable: boolean;
  fields: DocumentFields | null;
  review: { state: ReviewState; days_left: number | null; expiry_date: string | null };
  profile_hints: { age?: number };
}

export interface VaultDoc {
  id: string;
  doc_type: string;
  readable: boolean;
  fields: DocumentFields | null;
  fileName: string;
  addedAt: string;
  location: string;
  purpose: string;
}

export interface GuideField {
  label: string;
  value: string | null;
  hint: string;
}
export interface GuideStep {
  title: string;
  detail: string;
  fields: GuideField[];
}
export interface GuidePlan {
  title: string;
  steps: GuideStep[];
  grounded: boolean;
  apply_url: string | null;
}

export type Message =
  | { id: string; role: 'assistant'; kind: 'greeting' }
  | {
      id: string;
      role: 'assistant';
      kind: 'text';
      text: string;
      lang: string;
      mood: Mood;
      schemes: string[];
      guide: string | null;
      upload: string | null;
    }
  | { id: string; role: 'assistant'; kind: 'error'; code: string }
  | { id: string; role: 'user'; kind: 'text'; text: string };
