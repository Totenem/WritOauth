import type {
  AnalysisBreakdown,
  AnalysisResult,
  FeatureBreakdown,
  Paper,
  ProfileBreakdown,
  ProfileKey,
} from "@/types";

export function makeFeature(
  overrides: Partial<FeatureBreakdown> = {}
): FeatureBreakdown {
  return {
    key: "contraction_preference",
    label: "Contraction preference",
    kind: "scalar",
    measurement: "direct",
    weight: 0.1,
    note: "",
    available: true,
    suppressed_reason: null,
    z: 0.4,
    score: 92,
    submission: 0.2,
    baseline_mean: 0.18,
    baseline_stdev: 0.05,
    baseline_n: 3,
    ...overrides,
  };
}

export function makeProfile(
  overrides: Partial<ProfileBreakdown> = {}
): ProfileBreakdown {
  return {
    label: "Stylistic",
    score: 92,
    z: 0.4,
    weight: 0.3,
    available: true,
    suppressed_reason: null,
    features: [makeFeature()],
    ...overrides,
  };
}

const PROFILE_LABELS: Record<ProfileKey, string> = {
  lexical: "Lexical",
  syntactic: "Syntactic",
  grammatical: "Grammatical",
  mechanical: "Mechanical",
  stylistic: "Stylistic",
  discourse: "Discourse & Complexity",
};

export function makeBreakdown(
  overrides: Partial<AnalysisBreakdown> = {}
): AnalysisBreakdown {
  const profiles = Object.fromEntries(
    (Object.keys(PROFILE_LABELS) as ProfileKey[]).map((key) => [
      key,
      makeProfile({ label: PROFILE_LABELS[key] }),
    ])
  ) as Record<ProfileKey, ProfileBreakdown>;

  return {
    schema_version: 2,
    extractor_version: "2.0.0",
    overall: { z: 0.4, score: 92 },
    profiles,
    reliability: {
      confidence_level: 0.8,
      n_baseline_papers: 3,
      total_baseline_words: 1500,
      submission_word_count: 620,
      paragraphs_reliable: true,
    },
    threshold: 75,
    flagged: false,
    explanation:
      "This submission scores 92% and is consistent with the student's baseline.",
    ...overrides,
  };
}

export function makeAnalysis(
  overrides: Partial<AnalysisResult> = {}
): AnalysisResult {
  const breakdown = overrides.breakdown ?? makeBreakdown();
  return {
    id: 1,
    paper_id: 7,
    consistency_score: breakdown.overall.score,
    confidence_level: breakdown.reliability.confidence_level,
    flagged: breakdown.flagged,
    explanation: breakdown.explanation,
    ...overrides,
    breakdown,
  };
}

export function makePaper(overrides: Partial<Paper> = {}): Paper {
  return {
    id: 7,
    student_id: 1,
    subject_id: 2,
    type: "baseline",
    source_format: "paste",
    created_at: "2026-01-15T10:00:00Z",
    analysis_id: null,
    ...overrides,
  };
}
