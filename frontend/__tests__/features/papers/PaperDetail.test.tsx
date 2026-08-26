import { render, screen } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import PaperDetail from "@/features/papers/PaperDetail";
import * as paperService from "@/services/paper.service";
import * as studentService from "@/services/student.service";
import * as subjectService from "@/services/subject.service";

vi.mock("@/services/paper.service");
vi.mock("@/services/student.service");
vi.mock("@/services/subject.service");

function renderDetail(id: number) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  return render(
    <QueryClientProvider client={queryClient}>
      <PaperDetail id={id} />
    </QueryClientProvider>
  );
}

const basePaper = {
  id: 1,
  student_id: 1,
  subject_id: 5,
  created_at: "2024-01-01T00:00:00Z",
};

describe("PaperDetail", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(studentService.getStudents).mockResolvedValue([
      { id: 1, name: "Ana Cruz", created_at: "2024-01-01T00:00:00Z" },
    ]);
    vi.mocked(subjectService.getSubjects).mockResolvedValue([
      { id: 5, teacher_id: 1, name: "English 101", created_at: "2024-01-01T00:00:00Z" },
    ]);
  });

  it("shows a spinner while the paper loads", () => {
    vi.mocked(paperService.getPaper).mockReturnValue(new Promise(() => {}));

    renderDetail(1);

    expect(screen.getByRole("status", { name: "Loading" })).toBeDefined();
  });

  it("renders a baseline paper with its badge and resolved names", async () => {
    vi.mocked(paperService.getPaper).mockResolvedValue({
      ...basePaper,
      type: "baseline",
      analysis_id: null,
    });

    renderDetail(1);

    expect(await screen.findByText("Baseline")).toBeDefined();
    expect(await screen.findByText("Ana Cruz")).toBeDefined();
    expect(screen.getByText("English 101")).toBeDefined();
    expect(screen.getByText(/aren't\s+scored themselves/i)).toBeDefined();
  });

  it("links to the analysis for a scored submission", async () => {
    vi.mocked(paperService.getPaper).mockResolvedValue({
      ...basePaper,
      type: "submission",
      analysis_id: 42,
    });

    renderDetail(1);

    const link = await screen.findByRole("link", { name: /view analysis results/i });
    expect(link.getAttribute("href")).toBe("/analysis/42");
  });

  it("explains a submission with no analysis instead of linking nowhere", async () => {
    vi.mocked(paperService.getPaper).mockResolvedValue({
      ...basePaper,
      type: "submission",
      analysis_id: null,
    });

    renderDetail(1);

    expect(await screen.findByText(/no analysis for this submission/i)).toBeDefined();
    expect(screen.queryByRole("link", { name: /view analysis results/i })).toBeNull();
  });

  it("falls back to ids when the rosters don't resolve a name", async () => {
    vi.mocked(studentService.getStudents).mockResolvedValue([]);
    vi.mocked(subjectService.getSubjects).mockResolvedValue([]);
    vi.mocked(paperService.getPaper).mockResolvedValue({
      ...basePaper,
      type: "baseline",
      analysis_id: null,
    });

    renderDetail(1);

    expect(await screen.findByText("Student #1")).toBeDefined();
    expect(screen.getByText("Subject #5")).toBeDefined();
  });

  it("renders a not-found state for an unknown paper", async () => {
    vi.mocked(paperService.getPaper).mockRejectedValue({
      isAxiosError: true,
      response: { status: 404, data: { detail: "Paper 999 not found" } },
    });

    renderDetail(999);

    expect(await screen.findByText("Paper not found")).toBeDefined();
  });

  it("renders a not-found state for a non-numeric id without calling the API", () => {
    renderDetail(Number("abc"));

    expect(screen.getByText("Paper not found")).toBeDefined();
    expect(paperService.getPaper).not.toHaveBeenCalled();
  });
});
