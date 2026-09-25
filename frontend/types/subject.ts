export interface Subject {
  id: number;
  teacher_id: number;
  name: string;
  /** Unique, server-generated. Goes in the Subject Code column of the batch CSV. */
  course_code: string;
  /** Active enrollments only. */
  student_count: number;
  /** Active enrollments whose student has a complete (3-paper) baseline. */
  baseline_ready_count: number;
  created_at: string;
}

export interface CreateSubjectRequest {
  name: string;
}

export interface UpdateSubjectRequest {
  name: string;
}

export type EnrollmentStatus = "active" | "inactive";

export interface RosterStudent {
  id: number;
  name: string;
  email: string | null;
  status: EnrollmentStatus;
  baseline_paper_count: number;
  baseline_ready: boolean;
}

export interface Roster {
  subject_id: number;
  subject_name: string;
  course_code: string;
  students: RosterStudent[];
}

export interface BatchUploadResult {
  created_count: number;
  /** `row` is 1-based and counts the header as row 1, like a spreadsheet. */
  skipped: { row: number; reason: string }[];
}
