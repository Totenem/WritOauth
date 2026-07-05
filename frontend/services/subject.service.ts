import type { Subject, CreateSubjectRequest, UpdateSubjectRequest } from "@/types";

export async function getSubjects(): Promise<Subject[]> {
  throw new Error("not_implemented");
}

export async function getSubject(_id: number): Promise<Subject> {
  throw new Error("not_implemented");
}

export async function createSubject(_data: CreateSubjectRequest): Promise<Subject> {
  throw new Error("not_implemented");
}

export async function updateSubject(_id: number, _data: UpdateSubjectRequest): Promise<Subject> {
  throw new Error("not_implemented");
}

export async function deleteSubject(_id: number): Promise<void> {
  throw new Error("not_implemented");
}
