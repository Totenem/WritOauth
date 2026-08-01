"use client";

import { useMutation, useQuery } from "@tanstack/react-query";
import type { FeedbackRequest } from "@/types";
import * as analysisService from "@/services/analysis.service";

export const analysisQueryKey = (id: number) => ["analysis", id] as const;

/**
 * One analysis result. Reached by id — normally by being routed here straight
 * after a submission upload, via the paper's `analysis_id`.
 */
export function useAnalysis(id: number) {
  return useQuery({
    queryKey: analysisQueryKey(id),
    queryFn: () => analysisService.getAnalysis(id),
    enabled: Number.isFinite(id),
    retry: false,
  });
}

/**
 * Records the teacher's verdict on an analysis. The backend upserts on the
 * paper, so resubmitting is safe and simply replaces the previous decision —
 * a teacher is allowed to change their mind.
 */
export function useSubmitFeedback(analysisId: number) {
  return useMutation({
    mutationFn: (payload: FeedbackRequest) =>
      analysisService.submitFeedback(analysisId, payload),
  });
}
