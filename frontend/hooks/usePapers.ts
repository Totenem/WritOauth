"use client";

import { useMutation, useQuery } from "@tanstack/react-query";
import type { UploadAnalysisRequest, UploadBaselineRequest } from "@/types";
import type { PaperListFilters } from "@/services/paper.service";
import * as paperService from "@/services/paper.service";

export const paperQueryKey = (id: number) => ["papers", id] as const;
export const papersListQueryKey = (filters: PaperListFilters = {}) =>
  ["papers", "list", filters] as const;

/**
 * A single paper. There is no list endpoint on the backend (`/api/papers`
 * exposes only POST /baseline, POST /analyze and GET /{id}), so papers are
 * only ever reached by id — normally via the link shown after an upload.
 */
export function usePaper(id: number) {
  return useQuery({
    queryKey: paperQueryKey(id),
    queryFn: () => paperService.getPaper(id),
    enabled: Number.isFinite(id),
    retry: false,
  });
}

/**
 * Uploads a baseline sample. The backend builds/updates the student's baseline
 * profile off the back of this; that happens server-side and needs no extra
 * UI beyond confirming the upload landed.
 */
export function useUploadBaseline() {
  return useMutation({
    mutationFn: (payload: UploadBaselineRequest) => paperService.uploadBaseline(payload),
  });
}

/**
 * Uploads a submission for analysis. This scores synchronously against the
 * student's baseline, so the returned paper carries `analysis_id` when a
 * baseline existed — and null when one didn't.
 */
export function useUploadForAnalysis() {
  return useMutation({
    mutationFn: (payload: UploadAnalysisRequest) => paperService.uploadForAnalysis(payload),
  });
}

/** The caller's own papers, optionally filtered by student, subject or type. */
export function usePapersList(filters: PaperListFilters = {}, enabled = true) {
  return useQuery({
    queryKey: papersListQueryKey(filters),
    queryFn: () => paperService.listPapers(filters),
    enabled,
  });
}

/**
 * Extracts text from an uploaded document.
 *
 * A mutation rather than a query: it has no cacheable identity, and the
 * teacher reviews the result before anything is persisted.
 */
export function useExtractDocument() {
  return useMutation({
    mutationFn: (file: File) => paperService.extractDocument(file),
  });
}
