import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import PaperUploadForm from "@/features/papers/PaperUploadForm";
import * as studentService from "@/services/student.service";
import * as subjectService from "@/services/subject.service";

vi.mock("@/services/student.service");
vi.mock("@/services/subject.service");

function renderForm(props: Partial<React.ComponentProps<typeof PaperUploadForm>> = {}) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  return render(
    <QueryClientProvider client={queryClient}>
      <PaperUploadForm submitLabel="Upload" onSubmit={vi.fn()} {...props} />
    </QueryClientProvider>
  );
}

const mockStudents = [{ id: 1, name: "Ana Cruz", created_at: "2024-01-01T00:00:00Z" }];
const mockSubjects = [
  { id: 5, teacher_id: 1, name: "English 101", created_at: "2024-01-01T00:00:00Z" },
];

describe("PaperUploadForm", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(studentService.getStudents).mockResolvedValue(mockStudents);
    vi.mocked(subjectService.getSubjects).mockResolvedValue(mockSubjects);
  });

  it("shows a spinner while the pickers load", () => {
    vi.mocked(studentService.getStudents).mockReturnValue(new Promise(() => {}));

    renderForm();

    expect(screen.getByRole("status", { name: "Loading" })).toBeDefined();
  });

  it("populates the student and subject pickers from the rosters", async () => {
    renderForm();

    expect(await screen.findByLabelText("Student")).toBeDefined();
    expect(screen.getByRole("option", { name: "Ana Cruz" })).toBeDefined();
    expect(screen.getByRole("option", { name: "English 101" })).toBeDefined();
  });

  it("tells the teacher to add a student first when the roster is empty", async () => {
    vi.mocked(studentService.getStudents).mockResolvedValue([]);

    renderForm();

    expect(await screen.findByText("Add a student before uploading a paper.")).toBeDefined();
    expect(screen.queryByRole("button", { name: "Upload" })).toBeNull();
  });

  it("tells the teacher to add a subject first when they have none", async () => {
    vi.mocked(subjectService.getSubjects).mockResolvedValue([]);

    renderForm();

    expect(await screen.findByText("Add a subject before uploading a paper.")).toBeDefined();
  });

  it("asks for both when neither exists", async () => {
    vi.mocked(studentService.getStudents).mockResolvedValue([]);
    vi.mocked(subjectService.getSubjects).mockResolvedValue([]);

    renderForm();

    expect(
      await screen.findByText("Add a student and a subject before uploading a paper.")
    ).toBeDefined();
  });

  it("blocks submit and shows validation errors when nothing is filled in", async () => {
    const onSubmit = vi.fn();
    const user = userEvent.setup();
    renderForm({ onSubmit });

    await user.click(await screen.findByRole("button", { name: "Upload" }));

    // Deliberately distinct from the placeholder option text ("Select a
    // student"), so the error and the placeholder can't be confused.
    expect(await screen.findByText("Student is required")).toBeDefined();
    expect(screen.getByText("Subject is required")).toBeDefined();
    expect(screen.getByText("Content is required")).toBeDefined();
    expect(onSubmit).not.toHaveBeenCalled();
  });

  it("submits numeric ids and trimmed content", async () => {
    const onSubmit = vi.fn().mockResolvedValue(undefined);
    const user = userEvent.setup();
    renderForm({ onSubmit });

    await user.selectOptions(await screen.findByLabelText("Student"), "1");
    await user.selectOptions(screen.getByLabelText("Subject"), "5");
    await user.type(screen.getByLabelText("Content"), "  An essay about history.  ");
    await user.click(screen.getByRole("button", { name: "Upload" }));

    await waitFor(() =>
      expect(onSubmit).toHaveBeenCalledWith({
        student_id: 1,
        subject_id: 5,
        content: "An essay about history.",
      })
    );
  });

  it("rejects whitespace-only content", async () => {
    const onSubmit = vi.fn();
    const user = userEvent.setup();
    renderForm({ onSubmit });

    await user.selectOptions(await screen.findByLabelText("Student"), "1");
    await user.selectOptions(screen.getByLabelText("Subject"), "5");
    await user.type(screen.getByLabelText("Content"), "    ");
    await user.click(screen.getByRole("button", { name: "Upload" }));

    expect(await screen.findByText("Content is required")).toBeDefined();
    expect(onSubmit).not.toHaveBeenCalled();
  });

  it("renders an API error message", async () => {
    renderForm({
      error: {
        isAxiosError: true,
        response: { data: { detail: "Student 999 or subject 1 does not exist" } },
      },
    });

    expect(
      await screen.findByText("Student 999 or subject 1 does not exist")
    ).toBeDefined();
  });

  it("clears only the content on success, keeping the pickers set", async () => {
    const onSubmit = vi.fn().mockResolvedValue(undefined);
    const user = userEvent.setup();
    renderForm({ onSubmit, resetOnSuccess: true });

    const studentSelect = await screen.findByLabelText<HTMLSelectElement>("Student");
    await user.selectOptions(studentSelect, "1");
    await user.selectOptions(screen.getByLabelText("Subject"), "5");
    const content = screen.getByLabelText<HTMLTextAreaElement>("Content");
    await user.type(content, "An essay.");
    await user.click(screen.getByRole("button", { name: "Upload" }));

    await waitFor(() => expect(content.value).toBe(""));
    expect(studentSelect.value).toBe("1");
  });
});
