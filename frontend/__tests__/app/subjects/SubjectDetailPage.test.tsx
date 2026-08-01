import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import SubjectDetailPage from "@/app/(dashboard)/subjects/[id]/page";
import * as subjectService from "@/services/subject.service";

vi.mock("@/services/subject.service");

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
      <SubjectDetailPage params={{ id }} />
    </QueryClientProvider>
  );
}

const mockSubject = {
  id: 1,
  teacher_id: 1,
  name: "English 101",
  created_at: "2024-01-01T00:00:00Z",
};

describe("SubjectDetailPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("shows a spinner while the subject loads", () => {
    vi.mocked(subjectService.getSubject).mockReturnValue(new Promise(() => {}));

    renderPage();

    expect(screen.getByRole("status", { name: "Loading" })).toBeDefined();
  });

  it("renders the subject and pre-fills the edit form", async () => {
    vi.mocked(subjectService.getSubject).mockResolvedValue(mockSubject);

    renderPage();

    expect(
      await screen.findByRole("heading", { name: "English 101", level: 1 })
    ).toBeDefined();
    await waitFor(() =>
      expect(screen.getByLabelText<HTMLInputElement>("Name").value).toBe("English 101")
    );
  });

  it("renders a not-found state when the subject does not exist", async () => {
    vi.mocked(subjectService.getSubject).mockRejectedValue({
      isAxiosError: true,
      response: { status: 404, data: { detail: "Subject 999 not found" } },
    });

    renderPage("999");

    expect(
      await screen.findByRole("heading", { name: "Subject not found" })
    ).toBeDefined();
  });

  it("renders the same not-found state for another teacher's subject (plain 404)", async () => {
    // The backend returns 404 rather than 403 so existence isn't leaked; the UI
    // must not special-case it.
    vi.mocked(subjectService.getSubject).mockRejectedValue({
      isAxiosError: true,
      response: { status: 404, data: { detail: "Subject 7 not found" } },
    });

    renderPage("7");

    expect(
      await screen.findByRole("heading", { name: "Subject not found" })
    ).toBeDefined();
  });

  it("renders a not-found state for a non-numeric id without calling the API", () => {
    renderPage("abc");

    expect(screen.getByRole("heading", { name: "Subject not found" })).toBeDefined();
    expect(subjectService.getSubject).not.toHaveBeenCalled();
  });

  it("saves an edited name", async () => {
    vi.mocked(subjectService.getSubject).mockResolvedValue(mockSubject);
    vi.mocked(subjectService.updateSubject).mockResolvedValue({
      ...mockSubject,
      name: "English 102",
    });
    const user = userEvent.setup();

    renderPage();
    await screen.findByRole("heading", { name: "English 101", level: 1 });

    const input = screen.getByLabelText("Name");
    await user.clear(input);
    await user.type(input, "English 102");
    await user.click(screen.getByRole("button", { name: "Save changes" }));

    await waitFor(() =>
      expect(subjectService.updateSubject).toHaveBeenCalledWith(1, { name: "English 102" })
    );
  });

  it("deletes after confirmation and returns to the list", async () => {
    vi.mocked(subjectService.getSubject).mockResolvedValue(mockSubject);
    vi.mocked(subjectService.deleteSubject).mockResolvedValue(undefined);
    vi.stubGlobal("confirm", vi.fn().mockReturnValue(true));
    const user = userEvent.setup();

    renderPage();
    await screen.findByRole("heading", { name: "English 101", level: 1 });

    await user.click(screen.getByRole("button", { name: "Delete subject" }));

    await waitFor(() => expect(subjectService.deleteSubject).toHaveBeenCalledWith(1));
    await waitFor(() => expect(pushMock).toHaveBeenCalledWith("/subjects"));
  });

  it("does not delete when confirmation is dismissed", async () => {
    vi.mocked(subjectService.getSubject).mockResolvedValue(mockSubject);
    vi.stubGlobal("confirm", vi.fn().mockReturnValue(false));
    const user = userEvent.setup();

    renderPage();
    await screen.findByRole("heading", { name: "English 101", level: 1 });

    await user.click(screen.getByRole("button", { name: "Delete subject" }));

    expect(subjectService.deleteSubject).not.toHaveBeenCalled();
    expect(pushMock).not.toHaveBeenCalled();
  });
});
