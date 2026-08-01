"use client";

import { useCallback, useEffect } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import type { LoginRequest } from "@/types";
import * as authService from "@/services/auth.service";
import { clearToken, getToken } from "@/utils/tokenStorage";

export const AUTH_ME_QUERY_KEY = ["auth", "me"] as const;

/**
 * Central auth hook: tracks whether a teacher is logged in (backed by
 * GET /api/auth/me whenever a token is present), and exposes login/logout.
 */
export function useAuth() {
  const queryClient = useQueryClient();
  const hasToken = typeof window !== "undefined" && !!getToken();

  const meQuery = useQuery({
    queryKey: AUTH_ME_QUERY_KEY,
    queryFn: authService.getCurrentTeacher,
    enabled: hasToken,
    retry: false,
    staleTime: 5 * 60 * 1000,
  });

  // If the token is invalid/expired, /me will 401 — drop the stale token so
  // subsequent renders treat the user as logged out instead of looping.
  useEffect(() => {
    if (meQuery.isError) {
      clearToken();
    }
  }, [meQuery.isError]);

  const loginMutation = useMutation({
    mutationFn: (credentials: LoginRequest) => authService.login(credentials),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: AUTH_ME_QUERY_KEY });
    },
  });

  const logout = useCallback(async () => {
    await authService.logout();
    queryClient.removeQueries({ queryKey: AUTH_ME_QUERY_KEY });
  }, [queryClient]);

  const isLoading = hasToken && meQuery.isPending;
  const isAuthenticated = hasToken && !meQuery.isError && !!meQuery.data;

  return {
    teacher: meQuery.data,
    isLoading,
    isAuthenticated,
    login: loginMutation.mutateAsync,
    isLoggingIn: loginMutation.isPending,
    loginError: loginMutation.error,
    logout,
  };
}
