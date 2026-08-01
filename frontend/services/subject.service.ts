import type { Subject, CreateSubjectRequest, UpdateSubjectRequest } from "@/types";
import api from "./api";

export async function getSubjects(): Promise<Subject[]> {
  const { data } = await api.get<Subject[]>("/api/subjects");
  return data;
}

export async function getSubject(id: number): Promise<Subject> {
  const { data } = await api.get<Subject>(`/api/subjects/${id}`);
  return data;
}

export async function createSubject(payload: CreateSubjectRequest): Promise<Subject> {
  const { data } = await api.post<Subject>("/api/subjects", payload);
  return data;
}

export async function updateSubject(
  id: number,
  payload: UpdateSubjectRequest
): Promise<Subject> {
  const { data } = await api.put<Subject>(`/api/subjects/${id}`, payload);
  return data;
}

export async function deleteSubject(id: number): Promise<void> {
  await api.delete(`/api/subjects/${id}`);
}
