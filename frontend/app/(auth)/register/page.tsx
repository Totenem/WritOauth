import type { Metadata } from "next";
import { RegisterForm } from "@/features/authentication";

export const metadata: Metadata = { title: "Sign Up · WritOath" };

export default function RegisterPage() {
  return <RegisterForm />;
}
