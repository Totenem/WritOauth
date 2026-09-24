export interface DashboardCounts {
  students: number;
  subjects: number;
  baseline_papers: number;
  submissions: number;
  /**
   * Not equal to `submissions`: a submission from a student with no
   * baseline produces no analysis at all.
   */
  analyses: number;
}

export interface BaselineReadiness {
  ready: number;
  no_baseline: number;
  needs_more_samples: number;
}

/**
 * Two separate notions of "flagged", deliberately not merged: `ai_*` is the
 * engine's score against the threshold, `teacher_*` is what a human decided.
 */
export interface Verdicts {
  threshold: number;
  ai_flagged: number;
  ai_consistent: number;
  teacher_flagged: number;
  teacher_genuine: number;
  awaiting_review: number;
}

export interface StudentStat {
  student_id: number;
  name: string;
  submissions: number;
  flagged: number;
  genuine: number;
  average_score: number | null;
}

export interface SubjectStat {
  subject_id: number;
  name: string;
  submissions: number;
  flagged: number;
}

export interface RecentAnalysis {
  analysis_id: number;
  paper_id: number;
  student_id: number;
  student_name: string;
  subject_id: number;
  subject_name: string;
  consistency_score: number;
  flagged: boolean;
  teacher_decision: "genuine" | "flagged" | null;
  created_at: string;
}

export interface ScoreBucket {
  label: string;
  lower: number;
  upper: number;
  count: number;
}

export interface DashboardStats {
  counts: DashboardCounts;
  baseline_readiness: BaselineReadiness;
  verdicts: Verdicts;
  students_needing_attention: StudentStat[];
  most_consistent_students: StudentStat[];
  subjects: SubjectStat[];
  recent_activity: RecentAnalysis[];
  score_distribution: ScoreBucket[];
}
