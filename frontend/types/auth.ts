export interface LoginRequest {
  email: string;
  password: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
}

export interface Teacher {
  id: number;
  name: string;
  email: string;
  created_at: string;
}
