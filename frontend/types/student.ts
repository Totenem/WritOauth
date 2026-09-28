export interface SubjectSummary {
  id: number;
  name: string;
  course_code: string;
}

export interface Student {
  id: number;
  first_name: string;
  last_name: string;
  email: string | null;
  /** Server-computed "First Last", for anywhere that just displays a student. */
  name: string;
  subjects: SubjectSummary[];
  created_at: string;
}

export interface CreateStudentRequest {
  first_name: string;
  last_name: string;
  email: string | null;
  /** At least one - a student can't exist outside a course. */
  subject_ids: number[];
}

export interface UpdateStudentRequest {
  first_name: string;
  last_name: string;
  email: string | null;
}
