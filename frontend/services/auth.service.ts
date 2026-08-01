import type { LoginRequest, Teacher, TokenResponse } from "@/types";
import { clearToken, saveToken } from "@/utils/tokenStorage";
import api from "./api";

export async function login(credentials: LoginRequest): Promise<TokenResponse> {
  const { data } = await api.post<TokenResponse>("/api/auth/login", credentials);
  saveToken(data.access_token);
  return data;
}

export async function logout(): Promise<void> {
  // The backend's /api/auth/logout is a documented no-op for stateless JWT
  // (nothing to invalidate server-side), so logging out is purely a client-side
  // token clear.
  clearToken();
}

export async function getCurrentTeacher(): Promise<Teacher> {
  const { data } = await api.get<Teacher>("/api/auth/me");
  return data;
}
