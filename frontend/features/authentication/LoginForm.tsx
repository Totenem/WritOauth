"use client";

import { useForm } from "react-hook-form";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useAuth } from "@/hooks/useAuth";
import { Button, Card, Input } from "@/components";
import { getApiErrorMessage } from "@/utils/apiError";

interface LoginFormValues {
  email: string;
  password: string;
}

export default function LoginForm() {
  const router = useRouter();
  const { login, isLoggingIn, loginError } = useAuth();
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginFormValues>({ defaultValues: { email: "", password: "" } });

  const onSubmit = async (values: LoginFormValues) => {
    try {
      await login(values);
      router.push("/dashboard");
    } catch {
      // loginError from useAuth already surfaces the message below.
    }
  };

  return (
    <Card>
      <form onSubmit={handleSubmit(onSubmit)} noValidate className="space-y-4">
        <h2 className="text-xl font-semibold text-text">Sign In</h2>

        <Input
          label="Email"
          type="email"
          autoComplete="email"
          error={errors.email?.message}
          {...register("email", {
            required: "Email is required",
            pattern: {
              value: /^[^\s@]+@[^\s@]+\.[^\s@]+$/,
              message: "Enter a valid email address",
            },
          })}
        />

        <Input
          label="Password"
          type="password"
          autoComplete="current-password"
          error={errors.password?.message}
          {...register("password", { required: "Password is required" })}
        />

        {loginError && (
          <p role="alert" className="text-sm text-danger">
            {getApiErrorMessage(loginError)}
          </p>
        )}

        <Button type="submit" disabled={isLoggingIn} className="w-full">
          {isLoggingIn ? "Signing in..." : "Sign in"}
        </Button>

        <p className="text-center text-sm text-text-subtle">
          Don&apos;t have an account?{" "}
          <Link href="/register" className="text-primary-700 hover:underline">
            Create one
          </Link>
        </p>
      </form>
    </Card>
  );
}
