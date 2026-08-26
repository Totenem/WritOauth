import { createElement } from "react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderHook, waitFor, act } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useAuth } from "@/hooks/useAuth";
import * as authService from "@/services/auth.service";
import * as tokenStorage from "@/utils/tokenStorage";

vi.mock("@/services/auth.service");
vi.mock("@/utils/tokenStorage");

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });
  return function Wrapper({ children }: { children: React.ReactNode }) {
    return createElement(QueryClientProvider, { client: queryClient }, children);
  };
}

const mockTeacher = {
  id: 1,
  name: "Jane Teacher",
  email: "jane@example.com",
  created_at: "2024-01-01T00:00:00Z",
};

describe("useAuth", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(tokenStorage.getToken).mockReturnValue(null);
  });

  it("is not authenticated and does not call /me when there is no token", () => {
    const { result } = renderHook(() => useAuth(), { wrapper: createWrapper() });

    expect(result.current.isAuthenticated).toBe(false);
    expect(result.current.isLoading).toBe(false);
    expect(authService.getCurrentTeacher).not.toHaveBeenCalled();
  });

  it("persists a token via login and flips isAuthenticated once /me resolves", async () => {
    vi.mocked(authService.login).mockResolvedValue({
      access_token: "tok123",
      token_type: "bearer",
    });
    vi.mocked(authService.getCurrentTeacher).mockResolvedValue(mockTeacher);

    const { result, rerender } = renderHook(() => useAuth(), { wrapper: createWrapper() });

    await act(async () => {
      await result.current.login({ email: "jane@example.com", password: "secret" });
    });

    expect(authService.login).toHaveBeenCalledWith({
      email: "jane@example.com",
      password: "secret",
    });

    // Simulate the token now being present (as the real auth.service does via
    // saveToken) and the surrounding component re-rendering.
    vi.mocked(tokenStorage.getToken).mockReturnValue("tok123");
    rerender();

    await waitFor(() => expect(result.current.isAuthenticated).toBe(true));
    expect(result.current.teacher).toEqual(mockTeacher);
  });

  it("surfaces an error and stays unauthenticated when login fails", async () => {
    vi.mocked(authService.login).mockRejectedValue(new Error("Invalid credentials"));

    const { result } = renderHook(() => useAuth(), { wrapper: createWrapper() });

    await act(async () => {
      await expect(
        result.current.login({ email: "jane@example.com", password: "wrong" })
      ).rejects.toThrow("Invalid credentials");
    });

    await waitFor(() => expect(result.current.loginError).toBeTruthy());
    expect(result.current.isAuthenticated).toBe(false);
    expect(authService.getCurrentTeacher).not.toHaveBeenCalled();
  });

  it("logout clears the session", async () => {
    vi.mocked(authService.logout).mockResolvedValue(undefined);

    const { result } = renderHook(() => useAuth(), { wrapper: createWrapper() });

    await act(async () => {
      await result.current.logout();
    });

    expect(authService.logout).toHaveBeenCalled();
  });
});
