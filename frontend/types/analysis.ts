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
  remarks?: string;
}

export interface Feedback {
  id: number;
  paper_id: number;
  decision: FeedbackDecision;
  remarks?: string;
  created_at: string;
}
