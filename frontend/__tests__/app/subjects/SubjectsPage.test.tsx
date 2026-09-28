import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import SubjectsPage from "@/app/(dashboard)/subjects/page";
import * as subjectService from "@/services/subject.service";
import { makeSubject } from "../../fixtures/roster";

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

  it("renders the courses heading, the create action and an onboarding empty state", async () => {
    renderPage();

    expect(
      screen.getByRole("heading", { name: /Active Courses & Baseline Collection Policies/, level: 1 })
    ).toBeDefined();
    expect(screen.getByRole("button", { name: "Create New Course Group" })).toBeDefined();
    expect(await screen.findByText("No courses yet")).toBeDefined();
  });

  it("creates a course from the dialog and refetches the list", async () => {
    vi.mocked(subjectService.createSubject).mockResolvedValue(makeSubject({ name: "English 101" }));
    const user = userEvent.setup();

    renderPage();
    await screen.findByText("No courses yet");

    await user.click(screen.getByRole("button", { name: "Create New Course Group" }));
    const dialog = screen.getByRole("dialog");
    await user.type(within(dialog).getByLabelText("Name"), "English 101");
    await user.click(within(dialog).getByRole("button", { name: "Create course" }));

    await waitFor(() =>
      expect(subjectService.createSubject).toHaveBeenCalledWith({ name: "English 101" })
    );
    await waitFor(() => expect(screen.queryByRole("dialog")).toBeNull());
    await waitFor(() => expect(subjectService.getSubjects).toHaveBeenCalledTimes(2));
  });

  it("keeps the dialog open with the typed name when create fails", async () => {
    vi.mocked(subjectService.createSubject).mockRejectedValue({
      isAxiosError: true,
      response: { data: { detail: "Subject already exists" } },
    });
    const user = userEvent.setup();

    renderPage();
    await screen.findByText("No courses yet");

    await user.click(screen.getByRole("button", { name: "Create New Course Group" }));
    const dialog = screen.getByRole("dialog");
    const input = within(dialog).getByLabelText<HTMLInputElement>("Name");
    await user.type(input, "English 101");
    await user.click(within(dialog).getByRole("button", { name: "Create course" }));

    expect(await within(dialog).findByText("Subject already exists")).toBeDefined();
    expect(input.value).toBe("English 101");
  });
});
