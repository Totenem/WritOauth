"use client";

import { useForm } from "react-hook-form";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useAuth } from "@/hooks/useAuth";
import { Button, Card, Input } from "@/components";
import { getApiErrorMessage } from "@/utils/apiError";

interface RegisterFormValues {
  name: string;
  email: string;
  password: string;
  confirmPassword: string;
}

export default function RegisterForm() {
  const router = useRouter();
  const { register: registerTeacher, isRegistering, registerError } = useAuth();
  const {
    register,
    handleSubmit,
    watch,
    formState: { errors },
  } = useForm<RegisterFormValues>({
    defaultValues: { name: "", email: "", password: "", confirmPassword: "" },
  });

  const onSubmit = async (values: RegisterFormValues) => {
    try {
      await registerTeacher({
        name: values.name,
        email: values.email,
        password: values.password,
      });
      router.push("/dashboard");
    } catch {
      // registerError from useAuth already surfaces the message below.
    }
  };

  return (
    <Card>
      <form onSubmit={handleSubmit(onSubmit)} noValidate className="space-y-4">
        <h2 className="text-xl font-semibold text-text">Create Account</h2>

        <Input
          label="Name"
          type="text"
          autoComplete="name"
          error={errors.name?.message}
          {...register("name", { required: "Name is required" })}
        />

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
          autoComplete="new-password"
          error={errors.password?.message}
          {...register("password", {
            required: "Password is required",
            minLength: { value: 8, message: "Password must be at least 8 characters" },
          })}
        />

        <Input
          label="Confirm Password"
          type="password"
          autoComplete="new-password"
          error={errors.confirmPassword?.message}
          {...register("confirmPassword", {
            required: "Please confirm your password",
            validate: (value) =>
              value === watch("password") || "Passwords do not match",
          })}
        />

        {registerError && (
          <p role="alert" className="text-sm text-danger">
            {getApiErrorMessage(registerError)}
          </p>
        )}

        <Button type="submit" disabled={isRegistering} className="w-full">
          {isRegistering ? "Creating account..." : "Create account"}
        </Button>

        <p className="text-center text-sm text-text-subtle">
          Already have an account?{" "}
          <Link href="/login" className="text-primary-700 hover:underline">
            Sign in
          </Link>
        </p>
      </form>
    </Card>
  );
}
