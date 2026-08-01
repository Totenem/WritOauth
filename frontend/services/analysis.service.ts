import type { AnalysisResult, FeedbackRequest, Feedback } from "@/types";
import api from "./api";

export async function getAnalysis(id: number): Promise<AnalysisResult> {
  const { data } = await api.get<AnalysisResult>(`/api/analysis/${id}`);
  return data;
}

export async function submitFeedback(
  analysisId: number,
  payload: FeedbackRequest
): Promise<Feedback> {
  const { data } = await api.post<Feedback>(
    `/api/analysis/${analysisId}/feedback`,
    payload
  );
  return data;
}
