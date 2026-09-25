import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import StudentList from "@/features/students/StudentList";
import * as studentService from "@/services/student.service";
import { makeStudent } from "../../fixtures/roster";

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
  makeStudent({ id: 1, name: "Ana Cruz" }),
  makeStudent({ id: 2, name: "Ben Reyes" }),
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

  it("asks for confirmation before deleting", async () => {
    vi.mocked(studentService.getStudents).mockResolvedValue(mockStudents);
    const user = userEvent.setup();

    renderStudentList();
    await screen.findByText("Ana Cruz");

    await user.click(screen.getAllByRole("button", { name: "Delete" })[0]);

    // A dialog, not window.confirm: it can be styled, focus-trapped and
    // tested without stubbing a global.
    expect(screen.getByRole("dialog")).toBeDefined();
    expect(studentService.deleteStudent).not.toHaveBeenCalled();
  });

  it("deletes once the dialog is confirmed", async () => {
    vi.mocked(studentService.getStudents).mockResolvedValue(mockStudents);
    vi.mocked(studentService.deleteStudent).mockResolvedValue(undefined);
    const user = userEvent.setup();

    renderStudentList();
    await screen.findByText("Ana Cruz");
    await user.click(screen.getAllByRole("button", { name: "Delete" })[0]);

    await user.click(
      within(screen.getByRole("dialog")).getByRole("button", { name: "Delete" })
    );

    await waitFor(() => expect(studentService.deleteStudent).toHaveBeenCalledWith(1));
  });

  it("does not delete when the dialog is cancelled", async () => {
    vi.mocked(studentService.getStudents).mockResolvedValue(mockStudents);
    const user = userEvent.setup();

    renderStudentList();
    await screen.findByText("Ana Cruz");
    await user.click(screen.getAllByRole("button", { name: "Delete" })[0]);

    await user.click(screen.getByRole("button", { name: "Cancel" }));

    expect(screen.queryByRole("dialog")).toBeNull();
    expect(studentService.deleteStudent).not.toHaveBeenCalled();
  });
});
