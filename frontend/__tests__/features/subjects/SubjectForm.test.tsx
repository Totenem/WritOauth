import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi, beforeEach } from "vitest";
import SubjectForm from "@/features/subjects/SubjectForm";

describe("SubjectForm", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders a name field and the given submit label", () => {
    render(<SubjectForm onSubmit={vi.fn()} submitLabel="Add subject" />);

    expect(screen.getByLabelText("Name")).toBeDefined();
    expect(screen.getByRole("button", { name: "Add subject" })).toBeDefined();
  });

  it("blocks submit and shows a validation error when the name is empty", async () => {
    const onSubmit = vi.fn();
    const user = userEvent.setup();
    render(<SubjectForm onSubmit={onSubmit} submitLabel="Add subject" />);

    await user.click(screen.getByRole("button", { name: "Add subject" }));

    expect(await screen.findByText("Name is required")).toBeDefined();
    expect(onSubmit).not.toHaveBeenCalled();
  });

  it("rejects a whitespace-only name", async () => {
    const onSubmit = vi.fn();
    const user = userEvent.setup();
    render(<SubjectForm onSubmit={onSubmit} submitLabel="Add subject" />);

    await user.type(screen.getByLabelText("Name"), "   ");
    await user.click(screen.getByRole("button", { name: "Add subject" }));

    expect(await screen.findByText("Name is required")).toBeDefined();
    expect(onSubmit).not.toHaveBeenCalled();
  });

  it("submits the trimmed name", async () => {
    const onSubmit = vi.fn().mockResolvedValue(undefined);
    const user = userEvent.setup();
    render(<SubjectForm onSubmit={onSubmit} submitLabel="Add subject" />);

    await user.type(screen.getByLabelText("Name"), "  English 101  ");
    await user.click(screen.getByRole("button", { name: "Add subject" }));

    await waitFor(() => expect(onSubmit).toHaveBeenCalledWith({ name: "English 101" }));
  });

  it("pre-fills the field when editing an existing subject", () => {
    render(
      <SubjectForm defaultName="History 201" onSubmit={vi.fn()} submitLabel="Save" />
    );

    expect(screen.getByLabelText<HTMLInputElement>("Name").value).toBe("History 201");
  });

  it("shows a disabled saving state while submitting", () => {
    render(<SubjectForm onSubmit={vi.fn()} isSubmitting submitLabel="Add subject" />);

    const button = screen.getByRole("button", { name: "Saving..." });
    expect(button).toBeDefined();
    expect(button.hasAttribute("disabled")).toBe(true);
  });

  it("renders an API error message", () => {
    render(
      <SubjectForm
        onSubmit={vi.fn()}
        error={{
          isAxiosError: true,
          response: { data: { detail: "Subject already exists" } },
        }}
      />
    );

    expect(screen.getByRole("alert").textContent).toContain("Subject already exists");
  });

  it("clears the field after a successful submit when resetOnSuccess is set", async () => {
    const onSubmit = vi.fn().mockResolvedValue(undefined);
    const user = userEvent.setup();
    render(<SubjectForm onSubmit={onSubmit} submitLabel="Add subject" resetOnSuccess />);

    const input = screen.getByLabelText<HTMLInputElement>("Name");
    await user.type(input, "Science 301");
    await user.click(screen.getByRole("button", { name: "Add subject" }));

    await waitFor(() => expect(input.value).toBe(""));
  });
});
