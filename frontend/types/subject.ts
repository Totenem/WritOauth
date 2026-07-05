export interface Subject {
  id: number;
  teacher_id: number;
  name: string;
  created_at: string;
}

export interface CreateSubjectRequest {
  name: string;
}

export interface UpdateSubjectRequest {
  name: string;
}
