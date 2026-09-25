import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi, beforeEach } from "vitest";
import StudentForm from "@/features/students/StudentForm";

const courses = [
  { id: 1, name: "English 101", course_code: "ENGLIS-AB12" },
  { id: 2, name: "History 201", course_code: "HISTOR-CD34" },
];

async function fillName(user: ReturnType<typeof userEvent.setup>, first: string, last: string) {
  await user.type(screen.getByLabelText("First name"), first);
  await user.type(screen.getByLabelText("Last name"), last);
}

describe("StudentForm", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders name and email fields and the given submit label", () => {
    render(<StudentForm onSubmit={vi.fn()} submitLabel="Add student" />);

    expect(screen.getByLabelText("First name")).toBeDefined();
    expect(screen.getByLabelText("Last name")).toBeDefined();
    expect(screen.getByLabelText("Email (optional)")).toBeDefined();
    expect(screen.getByRole("button", { name: "Add student" })).toBeDefined();
  });

  it("blocks submit when first or last name is blank, including whitespace", async () => {
    const onSubmit = vi.fn();
    const user = userEvent.setup();
    render(<StudentForm onSubmit={onSubmit} submitLabel="Add student" />);

    await user.type(screen.getByLabelText("First name"), "   ");
    await user.click(screen.getByRole("button", { name: "Add student" }));

    expect(await screen.findByText("First name is required")).toBeDefined();
    expect(screen.getByText("Last name is required")).toBeDefined();
    expect(onSubmit).not.toHaveBeenCalled();
  });

  it("rejects a malformed email but allows leaving it blank", async () => {
    const onSubmit = vi.fn().mockResolvedValue(undefined);
    const user = userEvent.setup();
    render(<StudentForm onSubmit={onSubmit} submitLabel="Add student" />);

    await fillName(user, "Ana", "Cruz");
    await user.type(screen.getByLabelText("Email (optional)"), "not-an-email");
    await user.click(screen.getByRole("button", { name: "Add student" }));

    expect(await screen.findByText("Enter a valid email address")).toBeDefined();
    expect(onSubmit).not.toHaveBeenCalled();

    await user.clear(screen.getByLabelText("Email (optional)"));
    await user.click(screen.getByRole("button", { name: "Add student" }));

    await waitFor(() =>
      expect(onSubmit).toHaveBeenCalledWith({ first_name: "Ana", last_name: "Cruz", email: null })
    );
  });

  it("submits trimmed values", async () => {
    const onSubmit = vi.fn().mockResolvedValue(undefined);
    const user = userEvent.setup();
    render(<StudentForm onSubmit={onSubmit} submitLabel="Add student" />);

    await fillName(user, "  Ana ", " Cruz  ");
    await user.type(screen.getByLabelText("Email (optional)"), " ana@school.edu ");
    await user.click(screen.getByRole("button", { name: "Add student" }));

    await waitFor(() =>
      expect(onSubmit).toHaveBeenCalledWith({
        first_name: "Ana",
        last_name: "Cruz",
        email: "ana@school.edu",
      })
    );
  });

  it("requires at least one course when courses are offered", async () => {
    const onSubmit = vi.fn().mockResolvedValue(undefined);
    const user = userEvent.setup();
    render(<StudentForm subjects={courses} onSubmit={onSubmit} submitLabel="Add student" />);

    await fillName(user, "Ana", "Cruz");
    await user.click(screen.getByRole("button", { name: "Add student" }));

    expect(await screen.findByText("Choose at least one course")).toBeDefined();
    expect(onSubmit).not.toHaveBeenCalled();

    await user.click(screen.getByLabelText(/History 201/));
    await user.click(screen.getByRole("button", { name: "Add student" }));

    await waitFor(() =>
      expect(onSubmit).toHaveBeenCalledWith({
        first_name: "Ana",
        last_name: "Cruz",
        email: null,
        subject_ids: [2],
      })
    );
  });

  it("pre-ticks the only course when there is just one", async () => {
    const onSubmit = vi.fn().mockResolvedValue(undefined);
    const user = userEvent.setup();
    render(<StudentForm subjects={[courses[0]]} onSubmit={onSubmit} submitLabel="Add student" />);

    await fillName(user, "Ana", "Cruz");
    await user.click(screen.getByRole("button", { name: "Add student" }));

    await waitFor(() =>
      expect(onSubmit).toHaveBeenCalledWith(expect.objectContaining({ subject_ids: [1] }))
    );
  });

  it("pre-fills the fields when editing an existing student", () => {
    render(
      <StudentForm
        defaultValues={{ first_name: "Ben", last_name: "Reyes", email: "ben@school.edu" }}
        onSubmit={vi.fn()}
        submitLabel="Save"
      />
    );

    expect(screen.getByLabelText<HTMLInputElement>("First name").value).toBe("Ben");
    expect(screen.getByLabelText<HTMLInputElement>("Last name").value).toBe("Reyes");
    expect(screen.getByLabelText<HTMLInputElement>("Email (optional)").value).toBe(
      "ben@school.edu"
    );
    // Enrollment isn't edited here, so no course picker.
    expect(screen.queryByText("Enroll in")).toBeNull();
  });

  it("shows a disabled saving state while submitting", () => {
    render(<StudentForm onSubmit={vi.fn()} isSubmitting submitLabel="Add student" />);

    const button = screen.getByRole("button", { name: "Saving..." });
    expect(button.hasAttribute("disabled")).toBe(true);
  });

  it("renders an API error message", () => {
    render(
      <StudentForm
        onSubmit={vi.fn()}
        error={{ isAxiosError: true, response: { data: { detail: "Subject 9 not found" } } }}
      />
    );

    expect(screen.getByRole("alert").textContent).toContain("Subject 9 not found");
  });

  it("clears the fields after a successful submit when resetOnSuccess is set", async () => {
    const onSubmit = vi.fn().mockResolvedValue(undefined);
    const user = userEvent.setup();
    render(<StudentForm onSubmit={onSubmit} submitLabel="Add student" resetOnSuccess />);

    await fillName(user, "Cara", "Lim");
    await user.click(screen.getByRole("button", { name: "Add student" }));

    await waitFor(() =>
      expect(screen.getByLabelText<HTMLInputElement>("First name").value).toBe("")
    );
    expect(screen.getByLabelText<HTMLInputElement>("Last name").value).toBe("");
  });
});
