export interface BreakdownScore {
  vocabulary: number;
  sentence_structure: number;
  grammar: number;
  readability: number;
  style: number;
}

export interface AnalysisResult {
  id: number;
  paper_id: number;
  consistency_score: number;
  confidence_level: number;
  breakdown: BreakdownScore;
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
