"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import type { CreateStudentRequest, UpdateStudentRequest } from "@/types";
import * as studentService from "@/services/student.service";

export const STUDENTS_QUERY_KEY = ["students"] as const;

export const studentQueryKey = (id: number) => ["students", id] as const;

/** All students on the shared roster. */
export function useStudents() {
  return useQuery({
    queryKey: STUDENTS_QUERY_KEY,
    queryFn: studentService.getStudents,
  });
}

/** A single student. Disabled for a non-finite id so a bad URL param can't fire a request. */
export function useStudent(id: number) {
  return useQuery({
    queryKey: studentQueryKey(id),
    queryFn: () => studentService.getStudent(id),
    enabled: Number.isFinite(id),
    retry: false,
  });
}

export function useCreateStudent() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (payload: CreateStudentRequest) => studentService.createStudent(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: STUDENTS_QUERY_KEY });
    },
  });
}

export function useUpdateStudent() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, ...payload }: UpdateStudentRequest & { id: number }) =>
      studentService.updateStudent(id, payload),
    onSuccess: (student) => {
      queryClient.invalidateQueries({ queryKey: STUDENTS_QUERY_KEY });
      queryClient.invalidateQueries({ queryKey: studentQueryKey(student.id) });
    },
  });
}

export function useDeleteStudent() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: number) => studentService.deleteStudent(id),
    onSuccess: (_data, id) => {
      queryClient.removeQueries({ queryKey: studentQueryKey(id) });
      queryClient.invalidateQueries({ queryKey: STUDENTS_QUERY_KEY });
    },
  });
}
