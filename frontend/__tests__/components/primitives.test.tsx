import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import Alert from "@/components/Alert";
import EmptyState from "@/components/EmptyState";
import FileDropzone from "@/components/FileDropzone";
import Modal from "@/components/Modal";
import Progress from "@/components/Progress";
import Skeleton from "@/components/Skeleton";
import Spinner from "@/components/Spinner";
import { ToastProvider, useToast } from "@/components/Toast";

describe("Skeleton", () => {
  it("is announced exactly like a Spinner", () => {
    // Loading states across the app are asserted with
    // getByRole("status", { name: "Loading" }). Keeping the same contract is
    // what lets a Spinner be swapped for a Skeleton without touching tests.
    render(<Skeleton />);

    expect(screen.getByRole("status", { name: "Loading" })).toBeDefined();
  });

  it("matches the Spinner's accessible name", () => {
    const { unmount } = render(<Spinner />);
    const spinner = screen.getByRole("status").getAttribute("aria-label");
    unmount();

    render(<Skeleton />);

    expect(screen.getByRole("status").getAttribute("aria-label")).toBe(spinner);
  });
});

describe("EmptyState", () => {
  it("renders the title and description", () => {
    render(<EmptyState title="No students yet" description="Add your first one." />);

    expect(screen.getByText("No students yet")).toBeDefined();
    expect(screen.getByText("Add your first one.")).toBeDefined();
  });

  it("offers a way forward when given one", () => {
    render(
      <EmptyState title="No students yet" actionLabel="Add a student" actionHref="/students" />
    );

    const link = screen.getByRole("link", { name: "Add a student" });
    expect(link.getAttribute("href")).toBe("/students");
  });

  it("supports a callback action", async () => {
    const onAction = vi.fn();
    render(<EmptyState title="Nothing here" actionLabel="Retry" onAction={onAction} />);

    await userEvent.click(screen.getByRole("button", { name: "Retry" }));

    expect(onAction).toHaveBeenCalledOnce();
  });
});

describe("Alert", () => {
  it("announces errors assertively", () => {
    render(<Alert variant="danger">Something failed</Alert>);

    expect(screen.getByRole("alert").textContent).toContain("Something failed");
  });

  it("announces everything else politely", () => {
    render(<Alert variant="success">Saved</Alert>);

    expect(screen.getByRole("status").textContent).toContain("Saved");
  });
});

describe("Progress", () => {
  it("exposes its value to assistive tech", () => {
    render(<Progress value={40} label="Extracting" />);

    const bar = screen.getByRole("progressbar", { name: "Extracting" });
    expect(bar.getAttribute("aria-valuenow")).toBe("40");
  });

  it("omits a value when indeterminate", () => {
    render(<Progress label="Working" />);

    expect(screen.getByRole("progressbar").getAttribute("aria-valuenow")).toBeNull();
  });

  it("clamps out-of-range values", () => {
    render(<Progress value={180} label="Extracting" />);

    expect(screen.getByRole("progressbar").getAttribute("aria-valuenow")).toBe("100");
  });
});

describe("Modal", () => {
  it("renders nothing when closed", () => {
    render(<Modal open={false} onClose={vi.fn()} title="Delete student?" />);

    expect(screen.queryByRole("dialog")).toBeNull();
  });

  it("closes on Escape", async () => {
    const onClose = vi.fn();
    render(<Modal open onClose={onClose} title="Delete student?" />);

    await userEvent.keyboard("{Escape}");

    expect(onClose).toHaveBeenCalledOnce();
  });

  it("closes when the backdrop is clicked", async () => {
    const onClose = vi.fn();
    render(
      <Modal open onClose={onClose} title="Delete student?">
        <p>Body</p>
      </Modal>
    );

    const backdrop = document.querySelector('[aria-hidden="true"]');
    await userEvent.click(backdrop as Element);

    expect(onClose).toHaveBeenCalled();
  });

  it("is labelled by its title", () => {
    render(<Modal open onClose={vi.fn()} title="Delete student?" />);

    expect(screen.getByRole("dialog", { name: "Delete student?" })).toBeDefined();
  });

  it("moves focus into the dialog", async () => {
    render(
      <Modal open onClose={vi.fn()} title="Delete student?" footer={<button>Confirm</button>} />
    );

    await waitFor(() => {
      expect(document.activeElement?.textContent).toBe("Confirm");
    });
  });
});

describe("FileDropzone", () => {
  it("hands back the chosen file", async () => {
    const onFile = vi.fn();
    render(<FileDropzone onFile={onFile} />);

    const file = new File(["essay text"], "essay.txt", { type: "text/plain" });
    await userEvent.upload(screen.getByLabelText("Upload a document"), file);

    expect(onFile).toHaveBeenCalledWith(file);
  });

  it("is reachable by keyboard", () => {
    render(<FileDropzone onFile={vi.fn()} />);

    expect(screen.getByRole("button", { name: /drop a file here/i })).toBeDefined();
  });

  it("does not accept files while disabled", () => {
    render(<FileDropzone onFile={vi.fn()} disabled />);

    const input = screen.getByLabelText("Upload a document") as HTMLInputElement;
    expect(input.disabled).toBe(true);
  });
});

function ToastTrigger() {
  const { toast } = useToast();
  return (
    <>
      <button onClick={() => toast("Student saved")}>Save</button>
      <button onClick={() => toast("Save failed", "error")}>Fail</button>
    </>
  );
}

describe("Toast", () => {
  it("shows a confirmation", async () => {
    render(
      <ToastProvider>
        <ToastTrigger />
      </ToastProvider>
    );

    await userEvent.click(screen.getByRole("button", { name: "Save" }));

    expect(await screen.findByText("Student saved")).toBeDefined();
  });

  it("announces failures assertively", async () => {
    render(
      <ToastProvider>
        <ToastTrigger />
      </ToastProvider>
    );

    await userEvent.click(screen.getByRole("button", { name: "Fail" }));

    expect(await screen.findByRole("alert")).toBeDefined();
  });

  it("can be dismissed", async () => {
    render(
      <ToastProvider>
        <ToastTrigger />
      </ToastProvider>
    );
    await userEvent.click(screen.getByRole("button", { name: "Save" }));
    await screen.findByText("Student saved");

    await userEvent.click(screen.getByRole("button", { name: "Dismiss" }));

    await waitFor(() => {
      expect(screen.queryByText("Student saved")).toBeNull();
    });
  });

  it("does not throw outside a provider", async () => {
    // Components should stay unit-testable without wrapping them every time.
    render(<ToastTrigger />);

    await userEvent.click(screen.getByRole("button", { name: "Save" }));

    expect(screen.queryByText("Student saved")).toBeNull();
  });
});
