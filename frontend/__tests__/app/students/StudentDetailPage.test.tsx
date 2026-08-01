import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import StudentDetailPage from "@/app/(dashboard)/students/[id]/page";
import * as studentService from "@/services/student.service";

vi.mock("@/services/student.service");

const pushMock = vi.fn();
vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: pushMock }),
}));

function renderPage(id = "1") {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  return render(
    <QueryClientProvider client={queryClient}>
      <StudentDetailPage params={{ id }} />
    </QueryClientProvider>
  );
}

const mockStudent = { id: 1, name: "Ana Cruz", created_at: "2024-01-01T00:00:00Z" };

describe("StudentDetailPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("shows a spinner while the student loads", () => {
    vi.mocked(studentService.getStudent).mockReturnValue(new Promise(() => {}));

    renderPage();

    expect(screen.getByRole("status", { name: "Loading" })).toBeDefined();
  });

  it("renders the student and pre-fills the edit form", async () => {
    vi.mocked(studentService.getStudent).mockResolvedValue(mockStudent);

    renderPage();

    expect(await screen.findByRole("heading", { name: "Ana Cruz", level: 1 })).toBeDefined();
    await waitFor(() =>
      expect(screen.getByLabelText<HTMLInputElement>("Name").value).toBe("Ana Cruz")
    );
  });

  it("renders a not-found state when the student does not exist", async () => {
    vi.mocked(studentService.getStudent).mockRejectedValue({
      isAxiosError: true,
      response: { status: 404, data: { detail: "Student not found" } },
    });

    renderPage("999");

    expect(
      await screen.findByRole("heading", { name: "Student not found" })
    ).toBeDefined();
  });

  it("renders a not-found state for a non-numeric id without calling the API", () => {
    renderPage("abc");

    expect(screen.getByRole("heading", { name: "Student not found" })).toBeDefined();
    expect(studentService.getStudent).not.toHaveBeenCalled();
  });

  it("saves an edited name", async () => {
    vi.mocked(studentService.getStudent).mockResolvedValue(mockStudent);
    vi.mocked(studentService.updateStudent).mockResolvedValue({
      ...mockStudent,
      name: "Ana Cruz-Reyes",
    });
    const user = userEvent.setup();

    renderPage();
    await screen.findByRole("heading", { name: "Ana Cruz", level: 1 });

    const input = screen.getByLabelText("Name");
    await user.clear(input);
    await user.type(input, "Ana Cruz-Reyes");
    await user.click(screen.getByRole("button", { name: "Save changes" }));

    await waitFor(() =>
      expect(studentService.updateStudent).toHaveBeenCalledWith(1, {
        name: "Ana Cruz-Reyes",
      })
    );
  });

  it("deletes after confirmation and returns to the list", async () => {
    vi.mocked(studentService.getStudent).mockResolvedValue(mockStudent);
    vi.mocked(studentService.deleteStudent).mockResolvedValue(undefined);
    vi.stubGlobal("confirm", vi.fn().mockReturnValue(true));
    const user = userEvent.setup();

    renderPage();
    await screen.findByRole("heading", { name: "Ana Cruz", level: 1 });

    await user.click(screen.getByRole("button", { name: "Delete student" }));

    await waitFor(() => expect(studentService.deleteStudent).toHaveBeenCalledWith(1));
    await waitFor(() => expect(pushMock).toHaveBeenCalledWith("/students"));
  });

  it("does not delete when confirmation is dismissed", async () => {
    vi.mocked(studentService.getStudent).mockResolvedValue(mockStudent);
    vi.stubGlobal("confirm", vi.fn().mockReturnValue(false));
    const user = userEvent.setup();

    renderPage();
    await screen.findByRole("heading", { name: "Ana Cruz", level: 1 });

    await user.click(screen.getByRole("button", { name: "Delete student" }));

    expect(studentService.deleteStudent).not.toHaveBeenCalled();
    expect(pushMock).not.toHaveBeenCalled();
  });
});
