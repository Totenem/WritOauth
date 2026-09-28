"use client";

import { useForm } from "react-hook-form";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useAuth } from "@/hooks/useAuth";
import { getApiErrorMessage } from "@/utils/apiError";
import AuthField from "./AuthField";
import { AuthCard, FormError, GoogleButton, OrDivider, SubmitButton } from "./AuthCard";
import { ArrowRightIcon, LockIcon, MailIcon, UserIcon } from "@/components/icons";

interface RegisterFormValues {
  name: string;
  email: string;
  password: string;
  acceptTerms: boolean;
}

export default function RegisterForm() {
  const router = useRouter();
  const { register: registerTeacher, isRegistering, registerError } = useAuth();
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<RegisterFormValues>({
    defaultValues: { name: "", email: "", password: "", acceptTerms: false },
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
    <AuthCard title="Sign Up" subtitle="Create an educator account to evaluate authentic student work.">
      <form onSubmit={handleSubmit(onSubmit)} noValidate className="space-y-5">
        <AuthField
          label="Full Name"
          autoComplete="name"
          placeholder="Enter your name"
          icon={<UserIcon />}
          error={errors.name?.message}
          {...register("name", { required: "Name is required" })}
        />

        <AuthField
          label="Academic Email"
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
          autoComplete="new-password"
          placeholder="Enter your password"
          icon={<LockIcon />}
          error={errors.password?.message}
          {...register("password", {
            required: "Password is required",
            minLength: { value: 8, message: "Password must be at least 8 characters" },
          })}
        />

        <div>
          <label className="flex items-start gap-2.5 text-footnote text-brand-navy/80">
            <input
              type="checkbox"
              aria-invalid={errors.acceptTerms ? true : undefined}
              className="mt-0.5 h-4 w-4 shrink-0 rounded border-brand-gold-pale accent-brand-gold"
              {...register("acceptTerms", {
                required: "Please accept the terms to continue",
              })}
            />
            <span>
              I agree with the{" "}
              <span className="font-medium text-brand-blue">Terms of Use</span> and{" "}
              <span className="font-medium text-brand-blue">Academic Integrity Policy</span>
            </span>
          </label>
          {errors.acceptTerms && (
            <p className="mt-1.5 text-footnote text-red-600">{errors.acceptTerms.message}</p>
          )}
        </div>

        {registerError && <FormError message={getApiErrorMessage(registerError)} />}

        <SubmitButton busy={isRegistering}>
          {isRegistering ? "Creating account..." : "Sign Up"}
        </SubmitButton>

        <OrDivider />
        <GoogleButton />

        <p className="text-center text-footnote text-brand-navy/80">
          Already have an account?{" "}
          <Link
            href="/login"
            scroll={false}
            className="inline-flex items-center gap-0.5 font-semibold text-brand-blue hover:text-brand-blue-light"
          >
            Login <ArrowRightIcon className="h-3 w-3" />
          </Link>
        </p>
      </form>
    </AuthCard>
  );
}
