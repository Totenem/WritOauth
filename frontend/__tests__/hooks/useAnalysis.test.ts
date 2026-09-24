import { createElement } from "react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderHook, waitFor, act } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useAnalysis, useSubmitFeedback } from "@/hooks/useAnalysis";
import * as analysisService from "@/services/analysis.service";
import { makeAnalysis } from "../fixtures/analysis";

vi.mock("@/services/analysis.service");

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

const mockAnalysis = makeAnalysis({
  paper_id: 2,
  consistency_score: 97.7468,
  confidence_level: 0.333333,
});

describe("useAnalysis", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("fetches an analysis by id", async () => {
    vi.mocked(analysisService.getAnalysis).mockResolvedValue(mockAnalysis);

    const { result } = renderHook(() => useAnalysis(1), { wrapper: createWrapper() });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(analysisService.getAnalysis).toHaveBeenCalledWith(1);
    expect(result.current.data).toEqual(mockAnalysis);
  });

  it("does not fire a request for a non-numeric id", () => {
    renderHook(() => useAnalysis(Number("abc")), { wrapper: createWrapper() });

    expect(analysisService.getAnalysis).not.toHaveBeenCalled();
  });

  it("surfaces a 404 without retrying", async () => {
    vi.mocked(analysisService.getAnalysis).mockRejectedValue({
      isAxiosError: true,
      response: { status: 404, data: { detail: "Analysis 999 not found" } },
    });

    const { result } = renderHook(() => useAnalysis(999), { wrapper: createWrapper() });

    await waitFor(() => expect(result.current.isError).toBe(true));
    expect(analysisService.getAnalysis).toHaveBeenCalledTimes(1);
  });
});

describe("useSubmitFeedback", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("posts the decision and remarks for the given analysis", async () => {
    vi.mocked(analysisService.submitFeedback).mockResolvedValue({
      id: 1,
      paper_id: 2,
      decision: "flagged",
      remarks: "Vocabulary looks off.",
      created_at: "2024-01-01T00:00:00Z",
    });

    const { result } = renderHook(() => useSubmitFeedback(5), {
      wrapper: createWrapper(),
    });

    await act(async () => {
      await result.current.mutateAsync({
        decision: "flagged",
        remarks: "Vocabulary looks off.",
      });
    });

    expect(analysisService.submitFeedback).toHaveBeenCalledWith(5, {
      decision: "flagged",
      remarks: "Vocabulary looks off.",
    });
  });

  it("supports resubmitting a different decision (the backend upserts)", async () => {
    vi.mocked(analysisService.submitFeedback).mockResolvedValue({
      id: 1,
      paper_id: 2,
      decision: "genuine",
      remarks: null,
      created_at: "2024-01-01T00:00:00Z",
    });

    const { result } = renderHook(() => useSubmitFeedback(5), {
      wrapper: createWrapper(),
    });

    await act(async () => {
      await result.current.mutateAsync({ decision: "genuine", remarks: null });
    });

    await waitFor(() => expect(result.current.data?.decision).toBe("genuine"));
  });

  it("surfaces an error when the submission fails", async () => {
    vi.mocked(analysisService.submitFeedback).mockRejectedValue({
      isAxiosError: true,
      response: { status: 404, data: { detail: "Analysis 5 not found" } },
    });

    const { result } = renderHook(() => useSubmitFeedback(5), {
      wrapper: createWrapper(),
    });

    await act(async () => {
      await expect(
        result.current.mutateAsync({ decision: "genuine" })
      ).rejects.toBeTruthy();
    });

    await waitFor(() => expect(result.current.isError).toBe(true));
  });
});
