import type { Paper, UploadBaselineRequest, UploadAnalysisRequest } from "@/types";

export async function uploadBaseline(_data: UploadBaselineRequest): Promise<Paper> {
  throw new Error("not_implemented");
}

export async function uploadForAnalysis(_data: UploadAnalysisRequest): Promise<Paper> {
  throw new Error("not_implemented");
}

export async function getPaper(_id: number): Promise<Paper> {
  throw new Error("not_implemented");
}
