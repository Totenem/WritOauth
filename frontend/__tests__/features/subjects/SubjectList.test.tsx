import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import SubjectList from "@/features/subjects/SubjectList";
import * as subjectService from "@/services/subject.service";

vi.mock("@/services/subject.service");

function renderSubjectList() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  return render(
    <QueryClientProvider client={queryClient}>
      <SubjectList />
    </QueryClientProvider>
  );
}

const mockSubjects = [
  { id: 1, teacher_id: 1, name: "English 101", created_at: "2024-01-01T00:00:00Z" },
  { id: 2, teacher_id: 1, name: "History 201", created_at: "2024-01-02T00:00:00Z" },
];

describe("SubjectList", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("shows a spinner while loading", () => {
    vi.mocked(subjectService.getSubjects).mockReturnValue(new Promise(() => {}));

    renderSubjectList();

    expect(screen.getByRole("status", { name: "Loading" })).toBeDefined();
  });

  it("renders one entry per subject", async () => {
    vi.mocked(subjectService.getSubjects).mockResolvedValue(mockSubjects);

    renderSubjectList();

    expect(await screen.findByText("English 101")).toBeDefined();
    expect(screen.getByText("History 201")).toBeDefined();
  });

  it("shows an empty state when the teacher has no subjects", async () => {
    vi.mocked(subjectService.getSubjects).mockResolvedValue([]);

    renderSubjectList();

    expect(await screen.findByText(/no subjects yet/i)).toBeDefined();
  });

  it("shows the API error message when the list fails to load", async () => {
    vi.mocked(subjectService.getSubjects).mockRejectedValue({
      isAxiosError: true,
      response: { data: { detail: "Not authenticated" } },
    });

    renderSubjectList();

    expect(await screen.findByRole("alert")).toBeDefined();
    expect(screen.getByText("Not authenticated")).toBeDefined();
  });

  it("asks for confirmation before deleting", async () => {
    vi.mocked(subjectService.getSubjects).mockResolvedValue(mockSubjects);
    const user = userEvent.setup();

    renderSubjectList();
    await screen.findByText("English 101");

    await user.click(screen.getAllByRole("button", { name: "Delete" })[0]);

    // A dialog, not window.confirm: it can be styled, focus-trapped and
    // tested without stubbing a global.
    expect(screen.getByRole("dialog")).toBeDefined();
    expect(subjectService.deleteSubject).not.toHaveBeenCalled();
  });

  it("deletes once the dialog is confirmed", async () => {
    vi.mocked(subjectService.getSubjects).mockResolvedValue(mockSubjects);
    vi.mocked(subjectService.deleteSubject).mockResolvedValue(undefined);
    const user = userEvent.setup();

    renderSubjectList();
    await screen.findByText("English 101");
    await user.click(screen.getAllByRole("button", { name: "Delete" })[0]);

    await user.click(
      within(screen.getByRole("dialog")).getByRole("button", { name: "Delete" })
    );

    await waitFor(() => expect(subjectService.deleteSubject).toHaveBeenCalledWith(1));
  });

  it("does not delete when the dialog is cancelled", async () => {
    vi.mocked(subjectService.getSubjects).mockResolvedValue(mockSubjects);
    const user = userEvent.setup();

    renderSubjectList();
    await screen.findByText("English 101");
    await user.click(screen.getAllByRole("button", { name: "Delete" })[0]);

    await user.click(screen.getByRole("button", { name: "Cancel" }));

    expect(screen.queryByRole("dialog")).toBeNull();
    expect(subjectService.deleteSubject).not.toHaveBeenCalled();
  });
});
