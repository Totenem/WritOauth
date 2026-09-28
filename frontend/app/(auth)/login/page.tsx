import type { Metadata } from "next";
import { LoginForm } from "@/features/authentication";

export const metadata: Metadata = { title: "Sign In · WritOath" };

export default function LoginPage() {
  return <LoginForm />;
}
