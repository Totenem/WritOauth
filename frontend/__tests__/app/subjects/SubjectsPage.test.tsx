import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import SubjectsPage from "@/app/(dashboard)/subjects/page";
import * as subjectService from "@/services/subject.service";

vi.mock("@/services/subject.service");

function renderPage() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  return render(
    <QueryClientProvider client={queryClient}>
      <SubjectsPage />
    </QueryClientProvider>
  );
}

describe("SubjectsPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(subjectService.getSubjects).mockResolvedValue([]);
  });

  it("renders the heading, the add form and the list", async () => {
    renderPage();

    expect(screen.getByRole("heading", { name: "Subjects", level: 1 })).toBeDefined();
    expect(screen.getByRole("button", { name: "Add subject" })).toBeDefined();
    expect(await screen.findByText(/no subjects yet/i)).toBeDefined();
  });

  it("creates a subject and refetches the list", async () => {
    vi.mocked(subjectService.createSubject).mockResolvedValue({
      id: 1,
      teacher_id: 1,
      name: "English 101",
      created_at: "2024-01-01T00:00:00Z",
    });
    const user = userEvent.setup();

    renderPage();
    await screen.findByText(/no subjects yet/i);

    await user.type(screen.getByLabelText("Name"), "English 101");
    await user.click(screen.getByRole("button", { name: "Add subject" }));

    await waitFor(() =>
      expect(subjectService.createSubject).toHaveBeenCalledWith({ name: "English 101" })
    );
    await waitFor(() => expect(subjectService.getSubjects).toHaveBeenCalledTimes(2));
  });

  it("surfaces a create error without clearing the typed name", async () => {
    vi.mocked(subjectService.createSubject).mockRejectedValue({
      isAxiosError: true,
      response: { data: { detail: "Subject already exists" } },
    });
    const user = userEvent.setup();

    renderPage();
    await screen.findByText(/no subjects yet/i);

    const input = screen.getByLabelText<HTMLInputElement>("Name");
    await user.type(input, "English 101");
    await user.click(screen.getByRole("button", { name: "Add subject" }));

    expect(await screen.findByText("Subject already exists")).toBeDefined();
    expect(input.value).toBe("English 101");
  });
});
