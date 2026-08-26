import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import StudentList from "@/features/students/StudentList";
import * as studentService from "@/services/student.service";

vi.mock("@/services/student.service");

function renderStudentList() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  return render(
    <QueryClientProvider client={queryClient}>
      <StudentList />
    </QueryClientProvider>
  );
}

const mockStudents = [
  { id: 1, name: "Ana Cruz", created_at: "2024-01-01T00:00:00Z" },
  { id: 2, name: "Ben Reyes", created_at: "2024-01-02T00:00:00Z" },
];

describe("StudentList", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("shows a spinner while loading", () => {
    vi.mocked(studentService.getStudents).mockReturnValue(new Promise(() => {}));

    renderStudentList();

    expect(screen.getByRole("status", { name: "Loading" })).toBeDefined();
  });

  it("renders one entry per student", async () => {
    vi.mocked(studentService.getStudents).mockResolvedValue(mockStudents);

    renderStudentList();

    expect(await screen.findByText("Ana Cruz")).toBeDefined();
    expect(screen.getByText("Ben Reyes")).toBeDefined();
  });

  it("shows an empty state when the roster is empty", async () => {
    vi.mocked(studentService.getStudents).mockResolvedValue([]);

    renderStudentList();

    expect(await screen.findByText(/no students yet/i)).toBeDefined();
  });

  it("shows the API error message when the list fails to load", async () => {
    vi.mocked(studentService.getStudents).mockRejectedValue({
      isAxiosError: true,
      response: { data: { detail: "Not authenticated" } },
    });

    renderStudentList();

    expect(await screen.findByRole("alert")).toBeDefined();
    expect(screen.getByText("Not authenticated")).toBeDefined();
  });

  it("deletes a student after the confirm dialog is accepted", async () => {
    vi.mocked(studentService.getStudents).mockResolvedValue(mockStudents);
    vi.mocked(studentService.deleteStudent).mockResolvedValue(undefined);
    vi.stubGlobal("confirm", vi.fn().mockReturnValue(true));
    const user = userEvent.setup();

    renderStudentList();
    await screen.findByText("Ana Cruz");

    await user.click(screen.getAllByRole("button", { name: "Delete" })[0]);

    await waitFor(() => expect(studentService.deleteStudent).toHaveBeenCalledWith(1));
  });

  it("does not delete when the confirm dialog is dismissed", async () => {
    vi.mocked(studentService.getStudents).mockResolvedValue(mockStudents);
    vi.stubGlobal("confirm", vi.fn().mockReturnValue(false));
    const user = userEvent.setup();

    renderStudentList();
    await screen.findByText("Ana Cruz");

    await user.click(screen.getAllByRole("button", { name: "Delete" })[0]);

    expect(studentService.deleteStudent).not.toHaveBeenCalled();
  });
});
