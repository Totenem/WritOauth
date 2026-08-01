"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import type { CreateSubjectRequest, UpdateSubjectRequest } from "@/types";
import * as subjectService from "@/services/subject.service";

export const SUBJECTS_QUERY_KEY = ["subjects"] as const;

export const subjectQueryKey = (id: number) => ["subjects", id] as const;

/** Subjects owned by the logged-in teacher (the backend scopes this server-side). */
export function useSubjects() {
  return useQuery({
    queryKey: SUBJECTS_QUERY_KEY,
    queryFn: subjectService.getSubjects,
  });
}

/**
 * A single subject. Another teacher's subject comes back as a plain 404 (the
 * backend deliberately doesn't distinguish it from "missing"), so this needs no
 * ownership handling beyond the caller's normal not-found state.
 */
export function useSubject(id: number) {
  return useQuery({
    queryKey: subjectQueryKey(id),
    queryFn: () => subjectService.getSubject(id),
    enabled: Number.isFinite(id),
    retry: false,
  });
}

export function useCreateSubject() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (payload: CreateSubjectRequest) => subjectService.createSubject(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: SUBJECTS_QUERY_KEY });
    },
  });
}

export function useUpdateSubject() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, ...payload }: UpdateSubjectRequest & { id: number }) =>
      subjectService.updateSubject(id, payload),
    onSuccess: (subject) => {
      queryClient.invalidateQueries({ queryKey: SUBJECTS_QUERY_KEY });
      queryClient.invalidateQueries({ queryKey: subjectQueryKey(subject.id) });
    },
  });
}

export function useDeleteSubject() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: number) => subjectService.deleteSubject(id),
    onSuccess: (_data, id) => {
      queryClient.removeQueries({ queryKey: subjectQueryKey(id) });
      queryClient.invalidateQueries({ queryKey: SUBJECTS_QUERY_KEY });
    },
  });
}
