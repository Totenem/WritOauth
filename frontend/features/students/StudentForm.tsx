"use client";

import { useEffect } from "react";
import { useForm } from "react-hook-form";
import { Button, Input } from "@/components";
import { getApiErrorMessage } from "@/utils/apiError";

export interface StudentFormValues {
  name: string;
}

interface StudentFormProps {
  /** Pre-fills the name field — pass a student's current name to edit it. */
  defaultName?: string;
  onSubmit: (values: StudentFormValues) => Promise<unknown>;
  isSubmitting?: boolean;
  error?: unknown;
  submitLabel?: string;
  /** Renders a cancel button next to submit when provided. */
  onCancel?: () => void;
  /** Clears the field after a successful submit — wanted for create, not for edit. */
  resetOnSuccess?: boolean;
}

export default function StudentForm({
  defaultName = "",
  onSubmit,
  isSubmitting = false,
  error,
  submitLabel = "Save",
  onCancel,
  resetOnSuccess = false,
}: StudentFormProps) {
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<StudentFormValues>({ defaultValues: { name: defaultName } });

  // Keep the field in sync when the student loads asynchronously on the detail page.
  useEffect(() => {
    reset({ name: defaultName });
  }, [defaultName, reset]);

  const submit = async (values: StudentFormValues) => {
    try {
      await onSubmit({ name: values.name.trim() });
      if (resetOnSuccess) {
        reset({ name: "" });
      }
    } catch {
      // The `error` prop (mutation error) renders the message below.
    }
  };

  return (
    <form onSubmit={handleSubmit(submit)} noValidate className="space-y-4">
      <Input
        label="Name"
        placeholder="Student name"
        error={errors.name?.message}
        {...register("name", {
          required: "Name is required",
          validate: (value) => value.trim().length > 0 || "Name is required",
        })}
      />

      {error ? (
        <p role="alert" className="text-sm text-danger">
          {getApiErrorMessage(error)}
        </p>
      ) : null}

      <div className="flex gap-2">
        <Button type="submit" disabled={isSubmitting}>
          {isSubmitting ? "Saving..." : submitLabel}
        </Button>
        {onCancel ? (
          <Button type="button" variant="secondary" onClick={onCancel}>
            Cancel
          </Button>
        ) : null}
      </div>
    </form>
  );
}
