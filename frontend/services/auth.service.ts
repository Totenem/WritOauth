import type { LoginRequest, TokenResponse } from "@/types";

export async function login(_credentials: LoginRequest): Promise<TokenResponse> {
  throw new Error("not_implemented");
}

export async function logout(): Promise<void> {
  throw new Error("not_implemented");
}
