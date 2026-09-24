import { createElement } from "react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderHook, waitFor, act } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { usePaper, useUploadBaseline, useUploadForAnalysis } from "@/hooks/usePapers";
import * as paperService from "@/services/paper.service";

vi.mock("@/services/paper.service");

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });
  return function Wrapper({ children }: { children: React.ReactNode }) {
    return createElement(QueryClientProvider, { client: queryClient }, children);
  };
}

const baselinePaper = {
  id: 1,
  student_id: 1,
  subject_id: 1,
  type: "baseline" as const,
  source_format: "paste" as const,
  created_at: "2024-01-01T00:00:00Z",
  analysis_id: null,
};

const submissionPaper = {
  id: 2,
  student_id: 1,
  subject_id: 1,
  type: "submission" as const,
  source_format: "paste" as const,
  created_at: "2024-01-02T00:00:00Z",
  analysis_id: 7,
};

describe("usePaper", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("fetches a paper by id", async () => {
    vi.mocked(paperService.getPaper).mockResolvedValue(baselinePaper);

    const { result } = renderHook(() => usePaper(1), { wrapper: createWrapper() });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(paperService.getPaper).toHaveBeenCalledWith(1);
    expect(result.current.data).toEqual(baselinePaper);
  });

  it("does not fire a request for a non-numeric id", () => {
    renderHook(() => usePaper(Number("abc")), { wrapper: createWrapper() });

    expect(paperService.getPaper).not.toHaveBeenCalled();
  });

  it("surfaces a 404 without retrying", async () => {
    vi.mocked(paperService.getPaper).mockRejectedValue({
      isAxiosError: true,
      response: { status: 404, data: { detail: "Paper 999 not found" } },
    });

    const { result } = renderHook(() => usePaper(999), { wrapper: createWrapper() });

    await waitFor(() => expect(result.current.isError).toBe(true));
    expect(paperService.getPaper).toHaveBeenCalledTimes(1);
  });
});

describe("paper upload mutations", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("useUploadBaseline posts to the baseline endpoint", async () => {
    vi.mocked(paperService.uploadBaseline).mockResolvedValue(baselinePaper);

    const { result } = renderHook(() => useUploadBaseline(), { wrapper: createWrapper() });

    await act(async () => {
      const returned = await result.current.mutateAsync({
        student_id: 1,
        subject_id: 1,
        content: "Some baseline writing.",
      });
      expect(returned.analysis_id).toBeNull();
    });

    expect(paperService.uploadBaseline).toHaveBeenCalledWith({
      student_id: 1,
      subject_id: 1,
      content: "Some baseline writing.",
    });
  });

  it("useUploadForAnalysis returns the analysis_id when a baseline existed", async () => {
    vi.mocked(paperService.uploadForAnalysis).mockResolvedValue(submissionPaper);

    const { result } = renderHook(() => useUploadForAnalysis(), {
      wrapper: createWrapper(),
    });

    await act(async () => {
      const returned = await result.current.mutateAsync({
        student_id: 1,
        subject_id: 1,
        content: "Some submission.",
      });
      expect(returned.analysis_id).toBe(7);
    });
  });

  it("useUploadForAnalysis returns a null analysis_id when no baseline exists", async () => {
    vi.mocked(paperService.uploadForAnalysis).mockResolvedValue({
      ...submissionPaper,
      analysis_id: null,
    });

    const { result } = renderHook(() => useUploadForAnalysis(), {
      wrapper: createWrapper(),
    });

    await act(async () => {
      const returned = await result.current.mutateAsync({
        student_id: 1,
        subject_id: 1,
        content: "Some submission.",
      });
      expect(returned.analysis_id).toBeNull();
    });
  });

  it("surfaces a 400 for an invalid student or subject", async () => {
    vi.mocked(paperService.uploadForAnalysis).mockRejectedValue({
      isAxiosError: true,
      response: {
        status: 400,
        data: { detail: "Student 999 or subject 1 does not exist" },
      },
    });

    const { result } = renderHook(() => useUploadForAnalysis(), {
      wrapper: createWrapper(),
    });

    await act(async () => {
      await expect(
        result.current.mutateAsync({ student_id: 999, subject_id: 1, content: "x" })
      ).rejects.toBeTruthy();
    });

    await waitFor(() => expect(result.current.isError).toBe(true));
  });
});
