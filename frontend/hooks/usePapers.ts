"use client";

import { useMutation, useQuery } from "@tanstack/react-query";
import type { UploadAnalysisRequest, UploadBaselineRequest } from "@/types";
import * as paperService from "@/services/paper.service";

export const paperQueryKey = (id: number) => ["papers", id] as const;

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
