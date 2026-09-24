export type PaperType = "baseline" | "submission";

/**
 * Where a paper's text came from. The scoring engine suppresses
 * typography features when a submission's format differs from the
 * baselines', so a student isn't flagged for switching tools.
 */
export type SourceFormat = "paste" | "pdf" | "docx" | "txt";

export interface Paper {
  id: number;
  student_id: number;
  subject_id: number;
  type: PaperType;
  source_format: SourceFormat;
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
  source_format?: SourceFormat;
}

export interface UploadAnalysisRequest {
  student_id: number;
  subject_id: number;
  content: string;
  source_format?: SourceFormat;
}

/** Text pulled out of an uploaded document, for the teacher to review. */
export interface ExtractionResult {
  filename: string;
  source_format: SourceFormat;
  text: string;
  word_count: number;
  page_count: number | null;
  warnings: string[];
}
