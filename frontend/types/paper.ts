export type PaperType = "baseline" | "submission";

export interface Paper {
  id: number;
  student_id: number;
  subject_id: number;
  type: PaperType;
  created_at: string;
  /**
   * Set when an analysis was produced for this paper — i.e. on a submission
   * uploaded for a student who already has a baseline profile. Null for
   * baseline papers, and for submissions uploaded before any baseline exists.
   */
  analysis_id: number | null;
}

export interface UploadBaselineRequest {
  student_id: number;
  subject_id: number;
  content: string;
}

export interface UploadAnalysisRequest {
  student_id: number;
  subject_id: number;
  content: string;
}
