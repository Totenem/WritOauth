import type {
  ExtractionResult,
  Paper,
  PaperType,
  UploadAnalysisRequest,
  UploadBaselineRequest,
} from "@/types";
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

export interface PaperListFilters {
  student_id?: number;
  subject_id?: number;
  type?: PaperType;
  limit?: number;
  offset?: number;
}

export async function listPapers(filters: PaperListFilters = {}): Promise<Paper[]> {
  const { data } = await api.get<Paper[]>("/api/papers", { params: filters });
  return data;
}

/**
 * Pulls text out of an uploaded document so the teacher can review it
 * before it becomes a paper. Nothing is stored server-side by this call.
 */
export async function extractDocument(file: File): Promise<ExtractionResult> {
  const form = new FormData();
  form.append("file", file);
  const { data } = await api.post<ExtractionResult>("/api/papers/extract", form);
  return data;
}
