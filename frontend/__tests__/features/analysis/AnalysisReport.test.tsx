import { render, screen } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import AnalysisReport from "@/features/analysis/AnalysisReport";
import * as analysisService from "@/services/analysis.service";

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

const mockAnalysis = {
  id: 1,
  paper_id: 2,
  consistency_score: 97.7468,
  confidence_level: 0.333333,
  breakdown: {
    // Deliberately none of these round to 97.7%, so asserting on the headline
    // consistency score can't accidentally match a breakdown row instead.
    vocabulary: 94.7,
    sentence_structure: 88.6,
    grammar: 92.4,
    readability: 91.8,
    style: 96.3,
  },
  explanation:
    "This submission is 98% consistent with the student's baseline (flag threshold 75%).",
};

describe("AnalysisReport", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("shows a spinner while loading", () => {
    vi.mocked(analysisService.getAnalysis).mockReturnValue(new Promise(() => {}));

    renderReport(1);

    expect(screen.getByRole("status", { name: "Loading" })).toBeDefined();
  });

  it("renders the consistency score on a 0-100 scale", async () => {
    vi.mocked(analysisService.getAnalysis).mockResolvedValue(mockAnalysis);

    renderReport(1);

    // 97.7468 -> "97.7%", not "9774.7%".
    expect(await screen.findByText("97.7%")).toBeDefined();
  });

  it("shows the backend's explanation as the verdict text", async () => {
    vi.mocked(analysisService.getAnalysis).mockResolvedValue(mockAnalysis);

    renderReport(1);

    expect(await screen.findByText(mockAnalysis.explanation)).toBeDefined();
  });

  it("renders confidence_level as a 0-1 ratio, labelled as baseline strength", async () => {
    vi.mocked(analysisService.getAnalysis).mockResolvedValue(mockAnalysis);

    renderReport(1);

    // 0.333333 is a ratio, so it renders as 33.3% — and it is explicitly not
    // presented as a measure of suspicion.
    expect(await screen.findByText("33.3%")).toBeDefined();
    expect(screen.getByText("Baseline strength")).toBeDefined();
  });

  it("prompts for more baselines when strength is below full", async () => {
    vi.mocked(analysisService.getAnalysis).mockResolvedValue(mockAnalysis);

    renderReport(1);

    expect(
      await screen.findByRole("link", { name: "Upload more baseline papers" })
    ).toBeDefined();
  });

  it("drops the prompt once baseline strength is full", async () => {
    vi.mocked(analysisService.getAnalysis).mockResolvedValue({
      ...mockAnalysis,
      confidence_level: 1,
    });

    renderReport(1);

    await screen.findByText("100.0%");
    expect(screen.queryByRole("link", { name: "Upload more baseline papers" })).toBeNull();
  });

  it("links back to the submitted paper", async () => {
    vi.mocked(analysisService.getAnalysis).mockResolvedValue(mockAnalysis);

    renderReport(1);

    const link = await screen.findByRole("link", { name: /view submitted paper/i });
    expect(link.getAttribute("href")).toBe("/papers/2");
  });

  it("renders the breakdown and the feedback form", async () => {
    vi.mocked(analysisService.getAnalysis).mockResolvedValue(mockAnalysis);

    renderReport(1);

    expect(await screen.findByText("Breakdown")).toBeDefined();
    expect(screen.getAllByRole("meter")).toHaveLength(5);
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

  it("renders a not-found state for a non-numeric id without calling the API", () => {
    renderReport(Number("abc"));

    expect(screen.getByText("Analysis not found")).toBeDefined();
    expect(analysisService.getAnalysis).not.toHaveBeenCalled();
  });
});
