import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi, beforeEach } from "vitest";
import StudentForm from "@/features/students/StudentForm";

describe("StudentForm", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders a name field and the given submit label", () => {
    render(<StudentForm onSubmit={vi.fn()} submitLabel="Add student" />);

    expect(screen.getByLabelText("Name")).toBeDefined();
    expect(screen.getByRole("button", { name: "Add student" })).toBeDefined();
  });

  it("blocks submit and shows a validation error when the name is empty", async () => {
    const onSubmit = vi.fn();
    const user = userEvent.setup();
    render(<StudentForm onSubmit={onSubmit} submitLabel="Add student" />);

    await user.click(screen.getByRole("button", { name: "Add student" }));

    expect(await screen.findByText("Name is required")).toBeDefined();
    expect(onSubmit).not.toHaveBeenCalled();
  });

  it("rejects a whitespace-only name", async () => {
    const onSubmit = vi.fn();
    const user = userEvent.setup();
    render(<StudentForm onSubmit={onSubmit} submitLabel="Add student" />);

    await user.type(screen.getByLabelText("Name"), "   ");
    await user.click(screen.getByRole("button", { name: "Add student" }));

    expect(await screen.findByText("Name is required")).toBeDefined();
    expect(onSubmit).not.toHaveBeenCalled();
  });

  it("submits the trimmed name", async () => {
    const onSubmit = vi.fn().mockResolvedValue(undefined);
    const user = userEvent.setup();
    render(<StudentForm onSubmit={onSubmit} submitLabel="Add student" />);

    await user.type(screen.getByLabelText("Name"), "  Ana Cruz  ");
    await user.click(screen.getByRole("button", { name: "Add student" }));

    await waitFor(() => expect(onSubmit).toHaveBeenCalledWith({ name: "Ana Cruz" }));
  });

  it("pre-fills the field when editing an existing student", () => {
    render(<StudentForm defaultName="Ben Reyes" onSubmit={vi.fn()} submitLabel="Save" />);

    expect(screen.getByLabelText<HTMLInputElement>("Name").value).toBe("Ben Reyes");
  });

  it("shows a disabled saving state while submitting", () => {
    render(<StudentForm onSubmit={vi.fn()} isSubmitting submitLabel="Add student" />);

    const button = screen.getByRole("button", { name: "Saving..." });
    expect(button).toBeDefined();
    expect(button.hasAttribute("disabled")).toBe(true);
  });

  it("renders an API error message", () => {
    render(
      <StudentForm
        onSubmit={vi.fn()}
        error={{
          isAxiosError: true,
          response: { data: { detail: "Student already exists" } },
        }}
      />
    );

    expect(screen.getByRole("alert").textContent).toContain("Student already exists");
  });

  it("clears the field after a successful submit when resetOnSuccess is set", async () => {
    const onSubmit = vi.fn().mockResolvedValue(undefined);
    const user = userEvent.setup();
    render(<StudentForm onSubmit={onSubmit} submitLabel="Add student" resetOnSuccess />);

    const input = screen.getByLabelText<HTMLInputElement>("Name");
    await user.type(input, "Cara Lim");
    await user.click(screen.getByRole("button", { name: "Add student" }));

    await waitFor(() => expect(input.value).toBe(""));
  });
});
