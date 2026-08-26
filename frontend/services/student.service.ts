import type { Student, CreateStudentRequest, UpdateStudentRequest } from "@/types";
import api from "./api";

export async function getStudents(): Promise<Student[]> {
  const { data } = await api.get<Student[]>("/api/students");
  return data;
}

export async function getStudent(id: number): Promise<Student> {
  const { data } = await api.get<Student>(`/api/students/${id}`);
  return data;
}

export async function createStudent(payload: CreateStudentRequest): Promise<Student> {
  const { data } = await api.post<Student>("/api/students", payload);
  return data;
}

export async function updateStudent(
  id: number,
  payload: UpdateStudentRequest
): Promise<Student> {
  const { data } = await api.put<Student>(`/api/students/${id}`, payload);
  return data;
}

export async function deleteStudent(id: number): Promise<void> {
  await api.delete(`/api/students/${id}`);
}
