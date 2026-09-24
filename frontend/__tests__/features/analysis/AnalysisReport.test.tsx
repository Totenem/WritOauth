import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import AnalysisReport from "@/features/analysis/AnalysisReport";
import * as analysisService from "@/services/analysis.service";
import { makeAnalysis, makeBreakdown } from "../../fixtures/analysis";

vi.mock("@/services/analysis.service");

function renderReport(id: number) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  return render(
    <QueryClientProvider client={queryClient}>
      <AnalysisReport id={id} />
    </QueryClientProvider>
  );
}

// Deliberately distinct from every profile score, so asserting on the
// headline can't accidentally match a breakdown row instead.
const analysis = makeAnalysis({
  paper_id: 2,
  consistency_score: 97.7468,
  confidence_level: 0.333333,
  breakdown: makeBreakdown({
    overall: { z: 0.2, score: 97.7468 },
    explanation:
      "This submission scores 98% and is consistent with the student's baseline (flag threshold 75%).",
  }),
});

describe("AnalysisReport", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("shows a loading state", () => {
    vi.mocked(analysisService.getAnalysis).mockReturnValue(new Promise(() => {}));

    renderReport(1);

    expect(screen.getAllByRole("status", { name: "Loading" }).length).toBeGreaterThan(0);
  });

  it("renders the consistency score on a 0-100 scale", async () => {
    vi.mocked(analysisService.getAnalysis).mockResolvedValue(analysis);

    renderReport(1);

    // 97.7468 -> "97.7%", not "9774.7%".
    expect(await screen.findByText("97.7%")).toBeDefined();
  });

  it("shows the backend's explanation as the verdict text", async () => {
    vi.mocked(analysisService.getAnalysis).mockResolvedValue(analysis);

    renderReport(1);

    expect(await screen.findByText(analysis.explanation)).toBeDefined();
  });

  it("uses the server's flagged verdict rather than comparing scores itself", async () => {
    vi.mocked(analysisService.getAnalysis).mockResolvedValue(
      makeAnalysis({
        flagged: true,
        breakdown: makeBreakdown({ flagged: true, overall: { z: 3, score: 40 } }),
        consistency_score: 40,
      })
    );

    renderReport(1);

    expect(await screen.findByText("Needs review")).toBeDefined();
  });

  it("labels a consistent submission as such", async () => {
    vi.mocked(analysisService.getAnalysis).mockResolvedValue(analysis);

    renderReport(1);

    expect(await screen.findByText("Consistent")).toBeDefined();
  });

  it("renders confidence_level as a 0-1 ratio, labelled as baseline strength", async () => {
    vi.mocked(analysisService.getAnalysis).mockResolvedValue(analysis);

    renderReport(1);

    // 0.333333 is a ratio, so it renders as 33.3% - and it is explicitly not
    // presented as a measure of suspicion.
    expect(await screen.findByText("33.3%")).toBeDefined();
    expect(screen.getByText("Baseline strength")).toBeDefined();
  });

  it("prompts for more baselines when strength is below full", async () => {
    vi.mocked(analysisService.getAnalysis).mockResolvedValue(analysis);

    renderReport(1);

    expect(
      await screen.findByRole("link", { name: "Add more baseline papers" })
    ).toBeDefined();
  });

  it("drops the prompt once baseline strength is full", async () => {
    vi.mocked(analysisService.getAnalysis).mockResolvedValue(
      makeAnalysis({ ...analysis, confidence_level: 1 })
    );

    renderReport(1);

    await screen.findByText("100.0%");
    expect(
      screen.queryByRole("link", { name: "Add more baseline papers" })
    ).toBeNull();
  });

  it("warns when the comparison rests on a thin baseline", async () => {
    vi.mocked(analysisService.getAnalysis).mockResolvedValue(
      makeAnalysis({
        breakdown: makeBreakdown({
          reliability: {
            confidence_level: 0.2,
            n_baseline_papers: 1,
            total_baseline_words: 300,
            submission_word_count: 600,
            paragraphs_reliable: true,
          },
        }),
      })
    );

    renderReport(1);

    expect(await screen.findByText(/thin profile/)).toBeDefined();
  });

  it("warns when the submission is too short to measure reliably", async () => {
    vi.mocked(analysisService.getAnalysis).mockResolvedValue(
      makeAnalysis({
        breakdown: makeBreakdown({
          reliability: {
            confidence_level: 0.9,
            n_baseline_papers: 5,
            total_baseline_words: 3000,
            submission_word_count: 90,
            paragraphs_reliable: true,
          },
        }),
      })
    );

    renderReport(1);

    expect(await screen.findByText(/90 words this submission is short/)).toBeDefined();
  });

  it("stays quiet when the comparison is well supported", async () => {
    vi.mocked(analysisService.getAnalysis).mockResolvedValue(
      makeAnalysis({
        breakdown: makeBreakdown({
          reliability: {
            confidence_level: 1,
            n_baseline_papers: 5,
            total_baseline_words: 3000,
            submission_word_count: 800,
            paragraphs_reliable: true,
          },
        }),
      })
    );

    renderReport(1);

    await screen.findByText("Six authorship profiles");
    expect(screen.queryByText("Read this score with care")).toBeNull();
  });

  it("links back to the submitted paper", async () => {
    vi.mocked(analysisService.getAnalysis).mockResolvedValue(analysis);

    renderReport(1);

    const link = await screen.findByRole("link", { name: /view submitted paper/i });
    expect(link.getAttribute("href")).toBe("/papers/2");
  });

  it("renders the six profiles and the feedback form", async () => {
    vi.mocked(analysisService.getAnalysis).mockResolvedValue(analysis);

    renderReport(1);

    expect(await screen.findByText("Six authorship profiles")).toBeDefined();
    expect(screen.getAllByRole("meter")).toHaveLength(6);
    expect(screen.getByRole("radio", { name: /genuine/i })).toBeDefined();
  });

  it("renders a not-found state for an unknown analysis", async () => {
    vi.mocked(analysisService.getAnalysis).mockRejectedValue({
      isAxiosError: true,
      response: { status: 404, data: { detail: "Analysis 999 not found" } },
    });

    renderReport(999);

    expect(await screen.findByText("Analysis not found")).toBeDefined();
  });
});
