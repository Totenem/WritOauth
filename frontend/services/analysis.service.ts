import type { AnalysisResult, FeedbackRequest, Feedback } from "@/types";

export async function getAnalysis(_id: number): Promise<AnalysisResult> {
  throw new Error("not_implemented");
}

export async function submitFeedback(_analysisId: number, _data: FeedbackRequest): Promise<Feedback> {
  throw new Error("not_implemented");
}
