import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import LoginForm from "@/features/authentication/LoginForm";
import * as authService from "@/services/auth.service";

vi.mock("@/services/auth.service");
vi.mock("@/utils/tokenStorage");

const pushMock = vi.fn();
vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: pushMock }),
}));

function renderLoginForm() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  return render(
    <QueryClientProvider client={queryClient}>
      <LoginForm />
    </QueryClientProvider>
  );
}

describe("LoginForm", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders the sign in form", () => {
    renderLoginForm();
    expect(screen.getByRole("heading", { name: "Sign In" })).toBeDefined();
    expect(screen.getByLabelText("Email")).toBeDefined();
    expect(screen.getByLabelText("Password")).toBeDefined();
    expect(screen.getByRole("button", { name: /sign in/i })).toBeDefined();
  });

  it("shows validation errors and does not redirect on an empty submit", async () => {
    const user = userEvent.setup();
    renderLoginForm();

    await user.click(screen.getByRole("button", { name: /sign in/i }));

    expect(await screen.findByText("Email is required")).toBeDefined();
    expect(screen.getByText("Password is required")).toBeDefined();
    expect(authService.login).not.toHaveBeenCalled();
    expect(pushMock).not.toHaveBeenCalled();
  });

  it("calls login and redirects to the dashboard on a valid submit", async () => {
    vi.mocked(authService.login).mockResolvedValue({
      access_token: "tok123",
      token_type: "bearer",
    });
    const user = userEvent.setup();
    renderLoginForm();

    await user.type(screen.getByLabelText("Email"), "jane@example.com");
    await user.type(screen.getByLabelText("Password"), "secret123");
    await user.click(screen.getByRole("button", { name: /sign in/i }));

    await waitFor(() =>
      expect(authService.login).toHaveBeenCalledWith({
        email: "jane@example.com",
        password: "secret123",
      })
    );
    await waitFor(() => expect(pushMock).toHaveBeenCalledWith("/dashboard"));
  });

  it("shows the API error message and does not redirect when login fails", async () => {
    vi.mocked(authService.login).mockRejectedValue({
      isAxiosError: true,
      response: { data: { detail: "Invalid email or password" } },
    });
    const user = userEvent.setup();
    renderLoginForm();

    await user.type(screen.getByLabelText("Email"), "jane@example.com");
    await user.type(screen.getByLabelText("Password"), "wrongpass");
    await user.click(screen.getByRole("button", { name: /sign in/i }));

    expect(await screen.findByRole("alert")).toBeDefined();
    expect(pushMock).not.toHaveBeenCalled();
  });
});
