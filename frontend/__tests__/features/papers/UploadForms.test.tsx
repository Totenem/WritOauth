import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import BaselineUploadForm from "@/features/papers/BaselineUploadForm";
import AnalysisUploadForm from "@/features/papers/AnalysisUploadForm";
import * as paperService from "@/services/paper.service";
import * as studentService from "@/services/student.service";
import * as subjectService from "@/services/subject.service";

vi.mock("@/services/paper.service");
vi.mock("@/services/student.service");
vi.mock("@/services/subject.service");

const pushMock = vi.fn();
vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: pushMock }),
}));

function renderWithClient(ui: React.ReactElement) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  return render(<QueryClientProvider client={queryClient}>{ui}</QueryClientProvider>);
}

const mockStudents = [{ id: 1, name: "Ana Cruz", created_at: "2024-01-01T00:00:00Z" }];
const mockSubjects = [
  { id: 5, teacher_id: 1, name: "English 101", created_at: "2024-01-01T00:00:00Z" },
];

async function fillAndSubmit(buttonName: string) {
  const user = userEvent.setup();
  await user.selectOptions(await screen.findByLabelText("Student"), "1");
  await user.selectOptions(screen.getByLabelText("Subject"), "5");
  await user.type(screen.getByLabelText("Content"), "An essay about the war.");
  await user.click(screen.getByRole("button", { name: buttonName }));
}

describe("BaselineUploadForm", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(studentService.getStudents).mockResolvedValue(mockStudents);
    vi.mocked(subjectService.getSubjects).mockResolvedValue(mockSubjects);
  });

  it("uploads a baseline and confirms success with a link to the paper", async () => {
    vi.mocked(paperService.uploadBaseline).mockResolvedValue({
      id: 11,
      student_id: 1,
      subject_id: 5,
      type: "baseline",
      created_at: "2024-01-01T00:00:00Z",
      analysis_id: null,
    });

    renderWithClient(<BaselineUploadForm />);
    await fillAndSubmit("Upload baseline");

    await waitFor(() =>
      expect(paperService.uploadBaseline).toHaveBeenCalledWith({
        student_id: 1,
        subject_id: 5,
        content: "An essay about the war.",
      })
    );
    expect(await screen.findByRole("status")).toBeDefined();
    expect(screen.getByRole("link", { name: "View paper" }).getAttribute("href")).toBe(
      "/papers/11"
    );
  });

  it("shows the API error and no success banner when the upload fails", async () => {
    vi.mocked(paperService.uploadBaseline).mockRejectedValue({
      isAxiosError: true,
      response: { data: { detail: "Student 1 or subject 5 does not exist" } },
    });

    renderWithClient(<BaselineUploadForm />);
    await fillAndSubmit("Upload baseline");

    expect(
      await screen.findByText("Student 1 or subject 5 does not exist")
    ).toBeDefined();
    expect(screen.queryByRole("status")).toBeNull();
  });
});

describe("AnalysisUploadForm", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(studentService.getStudents).mockResolvedValue(mockStudents);
    vi.mocked(subjectService.getSubjects).mockResolvedValue(mockSubjects);
  });

  it("navigates to the analysis when the submission was scored", async () => {
    vi.mocked(paperService.uploadForAnalysis).mockResolvedValue({
      id: 12,
      student_id: 1,
      subject_id: 5,
      type: "submission",
      created_at: "2024-01-02T00:00:00Z",
      analysis_id: 42,
    });

    renderWithClient(<AnalysisUploadForm />);
    await fillAndSubmit("Upload for analysis");

    await waitFor(() => expect(pushMock).toHaveBeenCalledWith("/analysis/42"));
  });

  it("explains the missing baseline instead of linking nowhere when analysis_id is null", async () => {
    vi.mocked(paperService.uploadForAnalysis).mockResolvedValue({
      id: 13,
      student_id: 1,
      subject_id: 5,
      type: "submission",
      created_at: "2024-01-02T00:00:00Z",
      analysis_id: null,
    });

    renderWithClient(<AnalysisUploadForm />);
    await fillAndSubmit("Upload for analysis");

    expect(await screen.findByText(/no baseline\s+on file yet/i)).toBeDefined();
    expect(pushMock).not.toHaveBeenCalled();
    expect(
      screen.getByRole("link", { name: "Upload a baseline paper first" }).getAttribute("href")
    ).toBe("/papers/baseline");
  });

  it("shows the API error and does not navigate when the upload fails", async () => {
    vi.mocked(paperService.uploadForAnalysis).mockRejectedValue({
      isAxiosError: true,
      response: { data: { detail: "Student 999 or subject 5 does not exist" } },
    });

    renderWithClient(<AnalysisUploadForm />);
    await fillAndSubmit("Upload for analysis");

    expect(
      await screen.findByText("Student 999 or subject 5 does not exist")
    ).toBeDefined();
    expect(pushMock).not.toHaveBeenCalled();
  });
});
