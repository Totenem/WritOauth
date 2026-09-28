import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import RegisterForm from "@/features/authentication/RegisterForm";
import * as authService from "@/services/auth.service";

vi.mock("@/services/auth.service");
vi.mock("@/utils/tokenStorage");

const pushMock = vi.fn();
vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: pushMock }),
}));

function renderRegisterForm() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  return render(
    <QueryClientProvider client={queryClient}>
      <RegisterForm />
    </QueryClientProvider>
  );
}

async function fillValidForm(user: ReturnType<typeof userEvent.setup>) {
  await user.type(screen.getByLabelText("Full Name"), "Jane Teacher");
  await user.type(screen.getByLabelText("Academic Email"), "jane@example.com");
  await user.type(screen.getByLabelText("Password"), "secret123");
  await user.click(screen.getByRole("checkbox"));
}

describe("RegisterForm", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders the sign up form", () => {
    renderRegisterForm();
    expect(screen.getByRole("heading", { name: "Sign Up" })).toBeDefined();
    expect(screen.getByLabelText("Full Name")).toBeDefined();
    expect(screen.getByLabelText("Academic Email")).toBeDefined();
    expect(screen.getByLabelText("Password")).toBeDefined();
    expect(screen.getByRole("checkbox")).toBeDefined();
    expect(screen.getByRole("button", { name: /sign up/i })).toBeDefined();
  });

  it("shows validation errors and does not register on an empty submit", async () => {
    const user = userEvent.setup();
    renderRegisterForm();

    await user.click(screen.getByRole("button", { name: /sign up/i }));

    expect(await screen.findByText("Name is required")).toBeDefined();
    expect(screen.getByText("Email is required")).toBeDefined();
    expect(screen.getByText("Password is required")).toBeDefined();
    expect(screen.getByText("Please accept the terms to continue")).toBeDefined();
    expect(authService.register).not.toHaveBeenCalled();
    expect(pushMock).not.toHaveBeenCalled();
  });

  it("does not register until the terms are accepted", async () => {
    const user = userEvent.setup();
    renderRegisterForm();

    await user.type(screen.getByLabelText("Full Name"), "Jane Teacher");
    await user.type(screen.getByLabelText("Academic Email"), "jane@example.com");
    await user.type(screen.getByLabelText("Password"), "secret123");
    await user.click(screen.getByRole("button", { name: /sign up/i }));

    expect(await screen.findByText("Please accept the terms to continue")).toBeDefined();
    expect(authService.register).not.toHaveBeenCalled();
  });

  it("registers and redirects to the dashboard on a valid submit", async () => {
    vi.mocked(authService.register).mockResolvedValue({
      id: 1,
      name: "Jane Teacher",
      email: "jane@example.com",
      created_at: "2024-01-01T00:00:00Z",
    });
    vi.mocked(authService.login).mockResolvedValue({
      access_token: "tok123",
      token_type: "bearer",
    });
    const user = userEvent.setup();
    renderRegisterForm();

    await fillValidForm(user);
    await user.click(screen.getByRole("button", { name: /sign up/i }));

    await waitFor(() =>
      expect(authService.register).toHaveBeenCalledWith({
        name: "Jane Teacher",
        email: "jane@example.com",
        password: "secret123",
      })
    );
    await waitFor(() => expect(pushMock).toHaveBeenCalledWith("/dashboard"));
  });

  it("shows the API error message and does not redirect when registration fails", async () => {
    vi.mocked(authService.register).mockRejectedValue({
      isAxiosError: true,
      response: {
        data: { detail: "A teacher with email 'jane@example.com' already exists" },
      },
    });
    const user = userEvent.setup();
    renderRegisterForm();

    await fillValidForm(user);
    await user.click(screen.getByRole("button", { name: /sign up/i }));

    expect(await screen.findByRole("alert")).toBeDefined();
    expect(pushMock).not.toHaveBeenCalled();
  });
});
