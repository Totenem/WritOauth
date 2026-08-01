import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import StudentsPage from "@/app/(dashboard)/students/page";
import * as studentService from "@/services/student.service";

vi.mock("@/services/student.service");

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
  });

  it("renders the heading, the add form and the list", async () => {
    renderPage();

    expect(screen.getByRole("heading", { name: "Students", level: 1 })).toBeDefined();
    expect(screen.getByRole("button", { name: "Add student" })).toBeDefined();
    expect(await screen.findByText(/no students yet/i)).toBeDefined();
  });

  it("creates a student and refetches the roster", async () => {
    vi.mocked(studentService.createStudent).mockResolvedValue({
      id: 1,
      name: "Ana Cruz",
      created_at: "2024-01-01T00:00:00Z",
    });
    const user = userEvent.setup();

    renderPage();
    await screen.findByText(/no students yet/i);

    await user.type(screen.getByLabelText("Name"), "Ana Cruz");
    await user.click(screen.getByRole("button", { name: "Add student" }));

    await waitFor(() =>
      expect(studentService.createStudent).toHaveBeenCalledWith({ name: "Ana Cruz" })
    );
    // The list query is invalidated on success, so it refetches.
    await waitFor(() => expect(studentService.getStudents).toHaveBeenCalledTimes(2));
  });

  it("surfaces a create error without clearing the typed name", async () => {
    vi.mocked(studentService.createStudent).mockRejectedValue({
      isAxiosError: true,
      response: { data: { detail: "Name already taken" } },
    });
    const user = userEvent.setup();

    renderPage();
    await screen.findByText(/no students yet/i);

    const input = screen.getByLabelText<HTMLInputElement>("Name");
    await user.type(input, "Ana Cruz");
    await user.click(screen.getByRole("button", { name: "Add student" }));

    expect(await screen.findByText("Name already taken")).toBeDefined();
    expect(input.value).toBe("Ana Cruz");
  });
});
