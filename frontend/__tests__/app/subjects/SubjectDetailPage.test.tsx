import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import SubjectDetailPage from "@/app/(dashboard)/subjects/[id]/page";
import * as subjectService from "@/services/subject.service";
import type { Roster } from "@/types";
import { makeSubject } from "../../fixtures/roster";

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

const mockSubject = makeSubject({
  id: 1,
  name: "English 101",
  course_code: "ENGLIS-AB12",
  student_count: 2,
  baseline_ready_count: 1,
});

const mockRoster: Roster = {
  subject_id: 1,
  subject_name: "English 101",
  course_code: "ENGLIS-AB12",
  students: [
    {
      id: 10,
      name: "Grace Hopper",
      email: "grace@navy.mil",
      status: "active",
      baseline_paper_count: 3,
      baseline_ready: true,
    },
    {
      id: 11,
      name: "Ada Lovelace",
      email: null,
      status: "inactive",
      baseline_paper_count: 1,
      baseline_ready: false,
    },
  ],
};

describe("SubjectDetailPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(subjectService.getRoster).mockResolvedValue(mockRoster);
  });

  it("shows a skeleton while the course loads", () => {
    vi.mocked(subjectService.getSubject).mockReturnValue(new Promise(() => {}));

    renderPage();

    expect(screen.getByRole("status", { name: "Loading" })).toBeDefined();
  });

  it("renders the course code, counts and roster", async () => {
    vi.mocked(subjectService.getSubject).mockResolvedValue(mockSubject);

    renderPage();

    expect(await screen.findByRole("heading", { name: "English 101", level: 1 })).toBeDefined();
    expect(screen.getAllByText("ENGLIS-AB12").length).toBeGreaterThan(0);
    expect(screen.getByText(/2 active students · 1 baseline-locked/)).toBeDefined();

    const grace = (await screen.findByRole("link", { name: "Grace Hopper" })).closest("tr")!;
    expect(within(grace).getByText("grace@navy.mil")).toBeDefined();
    expect(within(grace).getByText("Locked")).toBeDefined();
    const ada = screen.getByRole("link", { name: "Ada Lovelace" }).closest("tr")!;
    expect(within(ada).getByText("inactive")).toBeDefined();
    expect(within(ada).getByText("1 / 3")).toBeDefined();
  });

  it("uploads a CSV and reports created and skipped rows", async () => {
    vi.mocked(subjectService.getSubject).mockResolvedValue(mockSubject);
    vi.mocked(subjectService.batchUploadStudents).mockResolvedValue({
      created_count: 2,
      skipped: [{ row: 4, reason: "Subject code 'X' doesn't match this course (ENGLIS-AB12)" }],
    });
    const user = userEvent.setup();

    const { container } = renderPage();
    await screen.findByRole("heading", { name: "English 101", level: 1 });

    const file = new File(["Subject Code,Last Name,First Name,Email,Status\n"], "roster.csv", {
      type: "text/csv",
    });
    await user.upload(container.querySelector<HTMLInputElement>('input[type="file"]')!, file);

    await waitFor(() =>
      expect(subjectService.batchUploadStudents).toHaveBeenCalledWith(1, file)
    );
    expect(await screen.findByText("Enrolled 2 students, skipped 1 row.")).toBeDefined();
    expect(screen.getByText("Row 4")).toBeDefined();
    expect(screen.getByText(/doesn't match this course/)).toBeDefined();
  });

  it("offers the CSV template for download", async () => {
    vi.mocked(subjectService.getSubject).mockResolvedValue(mockSubject);
    const createObjectURL = vi.fn().mockReturnValue("blob:template");
    const revokeObjectURL = vi.fn();
    Object.assign(URL, { createObjectURL, revokeObjectURL });
    const click = vi.spyOn(HTMLAnchorElement.prototype, "click").mockImplementation(() => {});
    const user = userEvent.setup();

    renderPage();
    await screen.findByRole("heading", { name: "English 101", level: 1 });
    await user.click(screen.getByRole("button", { name: "Download Template" }));

    const blob: Blob = createObjectURL.mock.calls[0][0];
    // jsdom's Blob has no .text(); FileReader is the portable way to read it.
    const text = await new Promise<string>((resolve) => {
      const reader = new FileReader();
      reader.onload = () => resolve(reader.result as string);
      reader.readAsText(blob);
    });
    expect(text).toBe("Subject Code,Last Name,First Name,Email,Status\r\n");
    expect(click).toHaveBeenCalled();
    expect(revokeObjectURL).toHaveBeenCalledWith("blob:template");
    click.mockRestore();
  });

  it("renders a not-found state when the course does not exist", async () => {
    vi.mocked(subjectService.getSubject).mockRejectedValue({
      isAxiosError: true,
      response: { status: 404, data: { detail: "Subject not found" } },
    });

    renderPage("999");

    expect(await screen.findByText("Course not found")).toBeDefined();
  });

  it("renders a not-found state for a non-numeric id without calling the API", () => {
    renderPage("abc");

    expect(screen.getByText("Course not found")).toBeDefined();
    expect(subjectService.getSubject).not.toHaveBeenCalled();
  });

  it("returns to the course list after deleting from settings", async () => {
    vi.mocked(subjectService.getSubject).mockResolvedValue(mockSubject);
    vi.mocked(subjectService.deleteSubject).mockResolvedValue(undefined);
    const user = userEvent.setup();

    renderPage();
    await screen.findByRole("heading", { name: "English 101", level: 1 });
    await user.click(screen.getByRole("button", { name: "Course settings" }));
    await user.click(screen.getByRole("button", { name: /Delete this course/ }));
    await user.click(within(screen.getByRole("dialog")).getByRole("button", { name: "Delete" }));

    await waitFor(() => expect(subjectService.deleteSubject).toHaveBeenCalledWith(1));
    await waitFor(() => expect(pushMock).toHaveBeenCalledWith("/subjects"));
  });
});
