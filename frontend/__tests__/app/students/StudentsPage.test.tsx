import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import StudentsPage from "@/app/(dashboard)/students/page";
import * as studentService from "@/services/student.service";
import * as subjectService from "@/services/subject.service";
import { makeStudent, makeSubject } from "../../fixtures/roster";

vi.mock("@/services/student.service");
vi.mock("@/services/subject.service");

function renderPage() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  return render(
    <QueryClientProvider client={queryClient}>
      <StudentsPage />
    </QueryClientProvider>
  );
}

describe("StudentsPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(studentService.getStudents).mockResolvedValue([]);
    vi.mocked(subjectService.getSubjects).mockResolvedValue([makeSubject({ id: 7 })]);
  });

  it("blocks adding students until the teacher has a course", async () => {
    vi.mocked(subjectService.getSubjects).mockResolvedValue([]);

    renderPage();

    expect(await screen.findByText("Create a course first")).toBeDefined();
    expect(screen.getByRole("link", { name: "Go to Courses" }).getAttribute("href")).toBe(
      "/subjects"
    );
    expect(screen.queryByRole("button", { name: "Add student" })).toBeNull();
  });

  it("renders the heading, the add form and the list once a course exists", async () => {
    renderPage();

    expect(screen.getByRole("heading", { name: "Students", level: 1 })).toBeDefined();
    expect(await screen.findByRole("button", { name: "Add student" })).toBeDefined();
    expect(await screen.findByText(/no students yet/i)).toBeDefined();
  });

  it("creates a student enrolled in the chosen course and refetches the roster", async () => {
    vi.mocked(studentService.createStudent).mockResolvedValue(makeStudent());
    const user = userEvent.setup();

    renderPage();
    await screen.findByRole("button", { name: "Add student" });

    await user.type(screen.getByLabelText("First name"), "Ana");
    await user.type(screen.getByLabelText("Last name"), "Cruz");
    await user.click(screen.getByRole("button", { name: "Add student" }));

    // A single course is pre-ticked, so the student is enrolled into it.
    await waitFor(() =>
      expect(studentService.createStudent).toHaveBeenCalledWith({
        first_name: "Ana",
        last_name: "Cruz",
        email: null,
        subject_ids: [7],
      })
    );
    await waitFor(() => expect(studentService.getStudents).toHaveBeenCalledTimes(2));
  });

  it("surfaces a create error without clearing the typed name", async () => {
    vi.mocked(studentService.createStudent).mockRejectedValue({
      isAxiosError: true,
      response: { data: { detail: "Subject 7 not found" } },
    });
    const user = userEvent.setup();

    renderPage();
    await screen.findByRole("button", { name: "Add student" });

    const input = screen.getByLabelText<HTMLInputElement>("First name");
    await user.type(input, "Ana");
    await user.type(screen.getByLabelText("Last name"), "Cruz");
    await user.click(screen.getByRole("button", { name: "Add student" }));

    expect(await screen.findByText("Subject 7 not found")).toBeDefined();
    expect(input.value).toBe("Ana");
  });
});
