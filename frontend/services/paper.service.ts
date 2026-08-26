import type { Paper, UploadBaselineRequest, UploadAnalysisRequest } from "@/types";
import api from "./api";

export async function uploadBaseline(payload: UploadBaselineRequest): Promise<Paper> {
  const { data } = await api.post<Paper>("/api/papers/baseline", payload);
  return data;
}

export async function uploadForAnalysis(payload: UploadAnalysisRequest): Promise<Paper> {
  const { data } = await api.post<Paper>("/api/papers/analyze", payload);
  return data;
}

export async function getPaper(id: number): Promise<Paper> {
  const { data } = await api.get<Paper>(`/api/papers/${id}`);
  return data;
}
