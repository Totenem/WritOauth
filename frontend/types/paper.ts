export type PaperType = "baseline" | "submission";

export interface Paper {
  id: number;
  student_id: number;
  subject_id: number;
  type: PaperType;
  created_at: string;
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
