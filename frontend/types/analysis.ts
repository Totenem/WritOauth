/** The six hand-built stylometric profiles - present on every analysis. */
export type StylometricProfileKey =
  | "lexical"
  | "syntactic"
  | "grammatical"
  | "mechanical"
  | "stylistic"
  | "discourse";

/**
 * Every profile the engine can report: the six stylometric ones plus the
 * LUAR neural style model ("AI Style Fingerprint"). The neural profile is
 * absent on analyses produced before it existed (extractor < 3.0.0).
 */
export type ProfileKey = "neural_style" | StylometricProfileKey;

/**
 * How trustworthy a single measurement is.
 *
 * "approximation" features are proxies with documented limits - the UI
 * badges them so a teacher doesn't read them as hard evidence.
 */
export type Measurement = "direct" | "approximation";

export type FeatureKind = "scalar" | "count" | "distribution";

export interface FeatureBreakdown {
  key: string;
  label: string;
  kind: FeatureKind;
  measurement: Measurement;
  weight: number;
  note: string;
  /** False when the submission was too short (or the wrong format) to measure this. */
  available: boolean;
  suppressed_reason: string | null;
  z: number;
  score: number | null;
  submission: number | null;
  baseline_mean: number | null;
  baseline_stdev: number | null;
  baseline_n: number | null;
}

export interface ProfileBreakdown {
  label: string;
  /** Null when every feature in the profile was suppressed. */
  score: number | null;
  z: number | null;
  weight: number;
  available: boolean;
  suppressed_reason: string | null;
  features: FeatureBreakdown[];
}

export interface OverallScore {
  z: number;
  score: number;
}

/**
 * How much weight this particular comparison can bear.
 *
 * Distinct from `confidence_level`, which describes the baseline. Keeping
 * them apart is what stops a 92% on a 120-word paragraph from looking as
 * solid as a 92% on a 900-word essay.
 */
export interface Reliability {
  confidence_level: number;
  n_baseline_papers: number;
  total_baseline_words: number;
  submission_word_count: number;
  paragraphs_reliable: boolean;
}

export interface AnalysisBreakdown {
  schema_version: number;
  extractor_version: string;
  overall: OverallScore;
  profiles: Record<StylometricProfileKey, ProfileBreakdown> & {
    neural_style?: ProfileBreakdown;
  };
  reliability: Reliability;
  threshold: number;
  /** Computed server-side - the client never infers a verdict itself. */
  flagged: boolean;
  explanation: string;
}

export interface AnalysisResult {
  id: number;
  paper_id: number;
  consistency_score: number;
  confidence_level: number;
  flagged: boolean;
  breakdown: AnalysisBreakdown;
  explanation: string;
}

export type FeedbackDecision = "genuine" | "flagged";

export interface FeedbackRequest {
  decision: FeedbackDecision;
  /** The API accepts `str | null`; null means "no remark", not an empty one. */
  remarks?: string | null;
}

export interface Feedback {
  id: number;
  paper_id: number;
  decision: FeedbackDecision;
  remarks: string | null;
  created_at: string;
}

/** Display order, strongest authorship signal first. */
export const PROFILE_ORDER: ProfileKey[] = [
  "neural_style",
  "stylistic",
  "syntactic",
  "lexical",
  "mechanical",
  "discourse",
  "grammatical",
];
