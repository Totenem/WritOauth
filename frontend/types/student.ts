export interface Student {
  id: number;
  name: string;
  created_at: string;
}

export interface CreateStudentRequest {
  name: string;
}

export interface UpdateStudentRequest {
  name: string;
}
