import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import FeedbackForm from "@/features/analysis/FeedbackForm";
import * as analysisService from "@/services/analysis.service";

vi.mock("@/services/analysis.service");

function renderForm(analysisId = 5) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  return render(
    <QueryClientProvider client={queryClient}>
      <FeedbackForm analysisId={analysisId} />
    </QueryClientProvider>
  );
}

describe("FeedbackForm", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("offers both decisions and an optional remarks box", () => {
    renderForm();

    expect(screen.getByRole("radio", { name: /genuine/i })).toBeDefined();
    expect(screen.getByRole("radio", { name: /flagged/i })).toBeDefined();
    expect(screen.getByLabelText("Remarks (optional)")).toBeDefined();
  });

  it("requires a decision before submitting", async () => {
    const user = userEvent.setup();
    renderForm();

    await user.click(screen.getByRole("button", { name: "Save decision" }));

    expect(await screen.findByText("Choose a decision")).toBeDefined();
    expect(analysisService.submitFeedback).not.toHaveBeenCalled();
  });

  it("submits a decision with remarks", async () => {
    vi.mocked(analysisService.submitFeedback).mockResolvedValue({
      id: 1,
      paper_id: 2,
      decision: "flagged",
      remarks: "Needs a chat.",
      created_at: "2024-01-01T00:00:00Z",
    });
    const user = userEvent.setup();
    renderForm(5);

    await user.click(screen.getByRole("radio", { name: /flagged/i }));
    await user.type(screen.getByLabelText("Remarks (optional)"), "Needs a chat.");
    await user.click(screen.getByRole("button", { name: "Save decision" }));

    await waitFor(() =>
      expect(analysisService.submitFeedback).toHaveBeenCalledWith(5, {
        decision: "flagged",
        remarks: "Needs a chat.",
      })
    );
  });

  it("sends null rather than an empty string when remarks are left blank", async () => {
    vi.mocked(analysisService.submitFeedback).mockResolvedValue({
      id: 1,
      paper_id: 2,
      decision: "genuine",
      remarks: null,
      created_at: "2024-01-01T00:00:00Z",
    });
    const user = userEvent.setup();
    renderForm(5);

    await user.click(screen.getByRole("radio", { name: /genuine/i }));
    await user.click(screen.getByRole("button", { name: "Save decision" }));

    await waitFor(() =>
      expect(analysisService.submitFeedback).toHaveBeenCalledWith(5, {
        decision: "genuine",
        remarks: null,
      })
    );
  });

  it("shows the recorded decision after a successful submit", async () => {
    vi.mocked(analysisService.submitFeedback).mockResolvedValue({
      id: 1,
      paper_id: 2,
      decision: "flagged",
      remarks: "Needs a chat.",
      created_at: "2024-01-15T00:00:00Z",
    });
    const user = userEvent.setup();
    renderForm();

    await user.click(screen.getByRole("radio", { name: /flagged/i }));
    await user.click(screen.getByRole("button", { name: "Save decision" }));

    const status = await screen.findByRole("status");
    expect(status.textContent).toContain("Flagged");
    expect(status.textContent).toContain("Needs a chat.");
    // Resubmitting is allowed, so the button becomes an update action.
    expect(screen.getByRole("button", { name: "Update decision" })).toBeDefined();
  });

  it("shows the API error and no success panel when submission fails", async () => {
    vi.mocked(analysisService.submitFeedback).mockRejectedValue({
      isAxiosError: true,
      response: { status: 404, data: { detail: "Analysis 5 not found" } },
    });
    const user = userEvent.setup();
    renderForm();

    await user.click(screen.getByRole("radio", { name: /genuine/i }));
    await user.click(screen.getByRole("button", { name: "Save decision" }));

    expect(await screen.findByRole("alert")).toBeDefined();
    expect(screen.getByText("Analysis 5 not found")).toBeDefined();
    expect(screen.queryByRole("status")).toBeNull();
  });
});
