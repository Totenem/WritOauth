import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import DashboardOverview from "@/features/dashboard/DashboardOverview";
import * as dashboardService from "@/services/dashboard.service";
import type { DashboardStats } from "@/types";

vi.mock("@/services/dashboard.service");

function renderOverview() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  return render(
    <QueryClientProvider client={queryClient}>
      <DashboardOverview />
    </QueryClientProvider>
  );
}

function makeStats(overrides: Partial<DashboardStats> = {}): DashboardStats {
  return {
    counts: {
      students: 4,
      subjects: 2,
      baseline_papers: 9,
      submissions: 6,
      analyses: 5,
    },
    baseline_readiness: { ready: 2, no_baseline: 1, needs_more_samples: 1 },
    verdicts: {
      threshold: 75,
      ai_flagged: 2,
      ai_consistent: 3,
      teacher_flagged: 1,
      teacher_genuine: 1,
      awaiting_review: 3,
    },
    students_needing_attention: [
      {
        student_id: 1,
        name: "Ana Cruz",
        submissions: 3,
        flagged: 2,
        genuine: 1,
        average_score: 54.2,
      },
    ],
    most_consistent_students: [
      {
        student_id: 2,
        name: "Ben Ortiz",
        submissions: 2,
        flagged: 0,
        genuine: 2,
        average_score: 93.4,
      },
    ],
    subjects: [
      { subject_id: 1, name: "English", submissions: 5, flagged: 2 },
    ],
    recent_activity: [
      {
        analysis_id: 10,
        paper_id: 20,
        student_id: 1,
        student_name: "Ana Cruz",
        subject_id: 1,
        subject_name: "English",
        consistency_score: 41.5,
        flagged: true,
        teacher_decision: "flagged",
        created_at: "2026-02-01T09:00:00Z",
      },
    ],
    score_distribution: [
      { label: "0-19", lower: 0, upper: 19, count: 1 },
      { label: "20-39", lower: 20, upper: 39, count: 0 },
      { label: "40-59", lower: 40, upper: 59, count: 1 },
      { label: "60-79", lower: 60, upper: 79, count: 1 },
      { label: "80-100", lower: 80, upper: 100, count: 2 },
    ],
    ...overrides,
  };
}

describe("DashboardOverview", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("shows a loading state", () => {
    vi.mocked(dashboardService.getDashboardStats).mockReturnValue(
      new Promise(() => {})
    );

    renderOverview();

    expect(screen.getByRole("status", { name: "Loading" })).toBeDefined();
  });

  it("onboards a brand-new teacher instead of showing zeroes", async () => {
    // This is the page a teacher lands on right after signing up.
    vi.mocked(dashboardService.getDashboardStats).mockResolvedValue(
      makeStats({
        counts: {
          students: 0,
          subjects: 0,
          baseline_papers: 0,
          submissions: 0,
          analyses: 0,
        },
      })
    );

    renderOverview();

    expect(await screen.findByText("Let's get set up")).toBeDefined();
    expect(
      screen.getByRole("link", { name: "Add your first student" })
    ).toBeDefined();
  });

  it("renders the headline counts", async () => {
    vi.mocked(dashboardService.getDashboardStats).mockResolvedValue(makeStats());

    renderOverview();

    expect(await screen.findByText("Students")).toBeDefined();
    expect(screen.getByText("Submissions checked")).toBeDefined();
  });

  it("surfaces students with no baseline as an actionable warning", async () => {
    vi.mocked(dashboardService.getDashboardStats).mockResolvedValue(makeStats());

    renderOverview();

    expect(await screen.findByText(/1 student has no baseline yet/)).toBeDefined();
  });

  it("flags submissions that were never analysed", async () => {
    // 6 submissions but only 5 analyses: one student had no baseline at the
    // time, so that paper was silently never scored.
    vi.mocked(dashboardService.getDashboardStats).mockResolvedValue(makeStats());

    renderOverview();

    expect(
      await screen.findByText(/1 submission was\s+saved without being analysed/)
    ).toBeDefined();
  });

  it("keeps the engine's verdict separate from the teacher's", async () => {
    vi.mocked(dashboardService.getDashboardStats).mockResolvedValue(makeStats());

    renderOverview();

    expect(await screen.findByText("Needs review")).toBeDefined();
    expect(screen.getByText("You: flagged")).toBeDefined();
  });

  it("links through to the student and to the analysis", async () => {
    vi.mocked(dashboardService.getDashboardStats).mockResolvedValue(makeStats());

    renderOverview();
    await screen.findByText("Needs a closer look");

    // The same student appears in the leaderboard and in recent activity,
    // each pointing somewhere different.
    const targets = screen
      .getAllByRole("link", { name: "Ana Cruz" })
      .map((link) => link.getAttribute("href"));

    expect(targets).toContain("/students/1");
    expect(targets).toContain("/analysis/10");
  });

  it("renders an error state", async () => {
    vi.mocked(dashboardService.getDashboardStats).mockRejectedValue({
      isAxiosError: true,
      response: { data: { detail: "Something broke" } },
    });

    renderOverview();

    expect(await screen.findByText("Something broke")).toBeDefined();
  });
});
