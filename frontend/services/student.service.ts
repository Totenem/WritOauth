import type { Student, CreateStudentRequest, UpdateStudentRequest } from "@/types";

export async function getStudents(): Promise<Student[]> {
  throw new Error("not_implemented");
}

export async function getStudent(_id: number): Promise<Student> {
  throw new Error("not_implemented");
}

export async function createStudent(_data: CreateStudentRequest): Promise<Student> {
  throw new Error("not_implemented");
}

export async function updateStudent(_id: number, _data: UpdateStudentRequest): Promise<Student> {
  throw new Error("not_implemented");
}

export async function deleteStudent(_id: number): Promise<void> {
  throw new Error("not_implemented");
}
