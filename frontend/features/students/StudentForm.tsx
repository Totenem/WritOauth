"use client";

import { useEffect } from "react";
import { useForm } from "react-hook-form";
import { Button, Input } from "@/components";
import type { SubjectSummary } from "@/types";
import { getApiErrorMessage } from "@/utils/apiError";

export interface StudentFormValues {
  first_name: string;
  last_name: string;
  email: string | null;
  /** Only present when the form is given `subjects` to choose from (i.e. creating). */
  subject_ids?: number[];
}

interface StudentFormProps {
  /** Pre-fills the fields - pass a student's current values to edit them. */
  defaultValues?: { first_name: string; last_name: string; email: string | null };
  /**
   * Courses to enroll into. When given, at least one must be ticked - a
   * student can't exist outside a course. Omit it when editing, since
   * enrollment isn't changed from this form.
   */
  subjects?: SubjectSummary[];
  onSubmit: (values: StudentFormValues) => Promise<unknown>;
  isSubmitting?: boolean;
  error?: unknown;
  submitLabel?: string;
  onCancel?: () => void;
  /** Clears the fields after a successful submit - wanted for create, not for edit. */
  resetOnSuccess?: boolean;
}

interface FieldValues {
  first_name: string;
  last_name: string;
  email: string;
  subject_ids: string[];
}

const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

export default function StudentForm({
  defaultValues,
  subjects,
  onSubmit,
  isSubmitting = false,
  error,
  submitLabel = "Save",
  onCancel,
  resetOnSuccess = false,
}: StudentFormProps) {
  // With a single course there's nothing to choose, so it's pre-ticked.
  const initialSubjects = subjects?.length === 1 ? [String(subjects[0].id)] : [];

  const empty: FieldValues = {
    first_name: defaultValues?.first_name ?? "",
    last_name: defaultValues?.last_name ?? "",
    email: defaultValues?.email ?? "",
    subject_ids: initialSubjects,
  };

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<FieldValues>({ defaultValues: empty });

  // Keep the fields in sync when the student loads asynchronously on the detail page.
  const first = defaultValues?.first_name;
  const last = defaultValues?.last_name;
  const email = defaultValues?.email;
  useEffect(() => {
    reset({ first_name: first ?? "", last_name: last ?? "", email: email ?? "", subject_ids: initialSubjects });
    // eslint-disable-next-line react-hooks/exhaustive-deps -- initialSubjects is derived from `subjects`
  }, [first, last, email, reset, subjects?.length]);

  const submit = async (values: FieldValues) => {
    const payload: StudentFormValues = {
      first_name: values.first_name.trim(),
      last_name: values.last_name.trim(),
      email: values.email.trim() || null,
    };
    if (subjects) {
      payload.subject_ids = (values.subject_ids || []).map(Number);
    }
    try {
      await onSubmit(payload);
      if (resetOnSuccess) {
        reset({ first_name: "", last_name: "", email: "", subject_ids: initialSubjects });
      }
    } catch {
      // The `error` prop (mutation error) renders the message below.
    }
  };

  const notBlank = (label: string) => (value: string) =>
    value.trim().length > 0 || `${label} is required`;

  return (
    <form onSubmit={handleSubmit(submit)} noValidate className="space-y-4">
      <div className="grid gap-4 sm:grid-cols-2">
        <Input
          label="First name"
          autoComplete="off"
          error={errors.first_name?.message}
          {...register("first_name", { validate: notBlank("First name") })}
        />
        <Input
          label="Last name"
          autoComplete="off"
          error={errors.last_name?.message}
          {...register("last_name", { validate: notBlank("Last name") })}
        />
      </div>

      <Input
        label="Email (optional)"
        type="email"
        autoComplete="off"
        error={errors.email?.message}
        {...register("email", {
          validate: (value) =>
            !value.trim() || EMAIL_PATTERN.test(value.trim()) || "Enter a valid email address",
        })}
      />

      {subjects ? (
        <fieldset>
          <legend className="mb-1.5 text-sm font-medium text-text-muted">Enroll in</legend>
          <div className="flex flex-wrap gap-2">
            {subjects.map((subject) => (
              <label
                key={subject.id}
                className="flex cursor-pointer items-center gap-2 rounded-lg border border-border-strong bg-bg px-3 py-2 text-footnote text-text has-[:checked]:border-primary-500 has-[:checked]:bg-primary-50"
              >
                <input
                  type="checkbox"
                  value={subject.id}
                  className="h-4 w-4 accent-primary-600"
                  {...register("subject_ids", {
                    validate: (value) =>
                      (Array.isArray(value) && value.length > 0) || "Choose at least one course",
                  })}
                />
                <span className="font-medium">{subject.name}</span>
                <span className="font-mono text-caption text-text-subtle">{subject.course_code}</span>
              </label>
            ))}
          </div>
          {errors.subject_ids ? (
            <p className="mt-1 text-sm text-danger">{errors.subject_ids.message}</p>
          ) : null}
        </fieldset>
      ) : null}

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
