"use client";

import { useForm } from "react-hook-form";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useAuth } from "@/hooks/useAuth";
import { getApiErrorMessage } from "@/utils/apiError";
import AuthField from "./AuthField";
import { AuthCard, FormError, GoogleButton, OrDivider, SubmitButton } from "./AuthCard";
import { ArrowRightIcon, LockIcon, MailIcon } from "@/components/icons";

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
    <AuthCard title="Sign In" subtitle="Welcome back. Log in to continue evaluating authentic student work.">
      <form onSubmit={handleSubmit(onSubmit)} noValidate className="space-y-5">
        <AuthField
          label="Email"
          type="email"
          autoComplete="email"
          placeholder="Enter your email"
          icon={<MailIcon />}
          error={errors.email?.message}
          {...register("email", {
            required: "Email is required",
            pattern: {
              value: /^[^\s@]+@[^\s@]+\.[^\s@]+$/,
              message: "Enter a valid email address",
            },
          })}
        />

        <AuthField
          label="Password"
          type="password"
          autoComplete="current-password"
          placeholder="Enter your password"
          icon={<LockIcon />}
          error={errors.password?.message}
          {...register("password", { required: "Password is required" })}
        />

        {loginError && <FormError message={getApiErrorMessage(loginError)} />}

        <SubmitButton busy={isLoggingIn}>{isLoggingIn ? "Signing in..." : "Sign In"}</SubmitButton>

        <OrDivider />
        <GoogleButton />

        <p className="text-center text-footnote text-brand-navy/80">
          Don&apos;t have an account?{" "}
          <Link
            href="/register"
            scroll={false}
            className="inline-flex items-center gap-0.5 font-semibold text-brand-blue hover:text-brand-blue-light"
          >
            Sign Up <ArrowRightIcon className="h-3 w-3" />
          </Link>
        </p>
      </form>
    </AuthCard>
  );
}
