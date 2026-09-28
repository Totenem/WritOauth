import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import SubjectList from "@/features/subjects/SubjectList";
import * as subjectService from "@/services/subject.service";
import { makeSubject } from "../../fixtures/roster";

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
  makeSubject({
    id: 1,
    name: "English 101",
    course_code: "ENGLIS-AB12",
    student_count: 38,
    baseline_ready_count: 36,
  }),
  makeSubject({ id: 2, name: "History 201", course_code: "HISTOR-CD34" }),
];

async function openDeleteDialog(user: ReturnType<typeof userEvent.setup>) {
  await user.click(screen.getByRole("button", { name: "Manage English 101" }));
  await user.click(screen.getByRole("button", { name: /Delete this course/ }));
}

describe("SubjectList", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("shows a skeleton while loading", () => {
    vi.mocked(subjectService.getSubjects).mockReturnValue(new Promise(() => {}));

    renderSubjectList();

    expect(screen.getByRole("status", { name: "Loading" })).toBeDefined();
  });

  it("renders a card per course with its code and baseline progress", async () => {
    vi.mocked(subjectService.getSubjects).mockResolvedValue(mockSubjects);

    renderSubjectList();

    expect(await screen.findByText("English 101")).toBeDefined();
    expect(screen.getByText("History 201")).toBeDefined();
    expect(screen.getByText("ENGLIS-AB12")).toBeDefined();
    expect(screen.getByText("36 / 38")).toBeDefined();
    expect(screen.getByLabelText("38 students enrolled")).toBeDefined();
    const links = screen.getAllByRole("link", { name: "View Roster" });
    expect(links[0].getAttribute("href")).toBe("/subjects/1");
  });

  it("shows an onboarding empty state when the teacher has no courses", async () => {
    vi.mocked(subjectService.getSubjects).mockResolvedValue([]);

    renderSubjectList();

    expect(await screen.findByText("No courses yet")).toBeDefined();
    expect(screen.getByRole("button", { name: "Create your first course" })).toBeDefined();
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

  it("renames a course from its settings", async () => {
    vi.mocked(subjectService.getSubjects).mockResolvedValue(mockSubjects);
    vi.mocked(subjectService.updateSubject).mockResolvedValue(
      makeSubject({ id: 1, name: "English 102" })
    );
    const user = userEvent.setup();

    renderSubjectList();
    await screen.findByText("English 101");
    await user.click(screen.getByRole("button", { name: "Manage English 101" }));

    const input = within(screen.getByRole("dialog")).getByLabelText("Name");
    await user.clear(input);
    await user.type(input, "English 102");
    await user.click(screen.getByRole("button", { name: "Save" }));

    await waitFor(() =>
      expect(subjectService.updateSubject).toHaveBeenCalledWith(1, { name: "English 102" })
    );
  });

  it("asks for confirmation before deleting", async () => {
    vi.mocked(subjectService.getSubjects).mockResolvedValue(mockSubjects);
    const user = userEvent.setup();

    renderSubjectList();
    await screen.findByText("English 101");
    await openDeleteDialog(user);

    expect(screen.getByRole("dialog", { name: "Delete English 101?" })).toBeDefined();
    expect(subjectService.deleteSubject).not.toHaveBeenCalled();
  });

  it("deletes once the dialog is confirmed", async () => {
    vi.mocked(subjectService.getSubjects).mockResolvedValue(mockSubjects);
    vi.mocked(subjectService.deleteSubject).mockResolvedValue(undefined);
    const user = userEvent.setup();

    renderSubjectList();
    await screen.findByText("English 101");
    await openDeleteDialog(user);

    await user.click(within(screen.getByRole("dialog")).getByRole("button", { name: "Delete" }));

    await waitFor(() => expect(subjectService.deleteSubject).toHaveBeenCalledWith(1));
  });

  it("does not delete when the dialog is cancelled", async () => {
    vi.mocked(subjectService.getSubjects).mockResolvedValue(mockSubjects);
    const user = userEvent.setup();

    renderSubjectList();
    await screen.findByText("English 101");
    await openDeleteDialog(user);

    await user.click(screen.getByRole("button", { name: "Cancel" }));

    expect(screen.queryByRole("dialog", { name: "Delete English 101?" })).toBeNull();
    expect(subjectService.deleteSubject).not.toHaveBeenCalled();
  });
});
