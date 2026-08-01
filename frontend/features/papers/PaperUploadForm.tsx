"use client";

import { useForm } from "react-hook-form";
import { Button, Select, Spinner, Textarea } from "@/components";
import { useStudents } from "@/hooks/useStudents";
import { useSubjects } from "@/hooks/useSubjects";
import { getApiErrorMessage } from "@/utils/apiError";

export interface PaperUploadValues {
  student_id: number;
  subject_id: number;
  content: string;
}

interface PaperUploadFormFields {
  student_id: string;
  subject_id: string;
  content: string;
}

interface PaperUploadFormProps {
  onSubmit: (values: PaperUploadValues) => Promise<unknown>;
  isSubmitting?: boolean;
  error?: unknown;
  submitLabel: string;
  contentHint?: string;
  /** Clears the textarea after a successful upload so the next one starts fresh. */
  resetOnSuccess?: boolean;
}

/**
 * The shared body of both upload forms: student picker, subject picker and a
 * content textarea. Baseline and submission uploads differ only in which
 * mutation they call and what they do afterwards, so that lives in the two
 * thin wrappers rather than being duplicated here.
 */
export default function PaperUploadForm({
  onSubmit,
  isSubmitting = false,
  error,
  submitLabel,
  contentHint,
  resetOnSuccess = false,
}: PaperUploadFormProps) {
  const students = useStudents();
  const subjects = useSubjects();

  const {
    register,
    handleSubmit,
    reset,
    getValues,
    formState: { errors },
  } = useForm<PaperUploadFormFields>({
    defaultValues: { student_id: "", subject_id: "", content: "" },
  });

  const submit = async (values: PaperUploadFormFields) => {
    try {
      await onSubmit({
        student_id: Number(values.student_id),
        subject_id: Number(values.subject_id),
        content: values.content.trim(),
      });
      if (resetOnSuccess) {
        // Keep the pickers where they are — a teacher uploading several papers
        // for one student shouldn't have to reselect every time.
        reset({ ...getValues(), content: "" });
      }
    } catch {
      // The `error` prop (mutation error) renders the message below.
    }
  };

  if (students.isPending || subjects.isPending) {
    return (
      <div className="flex justify-center py-8">
        <Spinner />
      </div>
    );
  }

  if (students.isError || subjects.isError) {
    return (
      <p role="alert" className="text-sm text-danger">
        {getApiErrorMessage(students.error ?? subjects.error)}
      </p>
    );
  }

  const hasStudents = students.data.length > 0;
  const hasSubjects = subjects.data.length > 0;

  // Without a student and a subject there is nothing valid to submit, so say so
  // plainly instead of rendering a form that can only fail.
  if (!hasStudents || !hasSubjects) {
    return (
      <p className="text-sm text-text-muted">
        {!hasStudents && !hasSubjects
          ? "Add a student and a subject before uploading a paper."
          : !hasStudents
            ? "Add a student before uploading a paper."
            : "Add a subject before uploading a paper."}
      </p>
    );
  }

  return (
    <form onSubmit={handleSubmit(submit)} noValidate className="space-y-4">
      <Select
        label="Student"
        placeholder="Select a student"
        error={errors.student_id?.message}
        options={students.data.map((student) => ({
          value: student.id,
          label: student.name,
        }))}
        {...register("student_id", { required: "Student is required" })}
      />

      <Select
        label="Subject"
        placeholder="Select a subject"
        error={errors.subject_id?.message}
        options={subjects.data.map((subject) => ({
          value: subject.id,
          label: subject.name,
        }))}
        {...register("subject_id", { required: "Subject is required" })}
      />

      <Textarea
        label="Content"
        placeholder="Paste the student's writing here..."
        hint={contentHint}
        error={errors.content?.message}
        {...register("content", {
          required: "Content is required",
          validate: (value) => value.trim().length > 0 || "Content is required",
        })}
      />

      {error ? (
        <p role="alert" className="text-sm text-danger">
          {getApiErrorMessage(error)}
        </p>
      ) : null}

      <Button type="submit" disabled={isSubmitting}>
        {isSubmitting ? "Uploading..." : submitLabel}
      </Button>
    </form>
  );
}
