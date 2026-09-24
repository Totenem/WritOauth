"use client";

import { useState } from "react";
import { useForm } from "react-hook-form";

import {
  Alert,
  Button,
  EmptyState,
  FileDropzone,
  Progress,
  Select,
  SkeletonBar,
  SkeletonGroup,
  Spinner,
  Textarea,
} from "@/components";
import { useExtractDocument } from "@/hooks/usePapers";
import { useStudents } from "@/hooks/useStudents";
import { useSubjects } from "@/hooks/useSubjects";
import type { SourceFormat } from "@/types";
import { getApiErrorMessage } from "@/utils/apiError";

export interface PaperUploadValues {
  student_id: number;
  subject_id: number;
  content: string;
  source_format: SourceFormat;
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
 * The shared body of both upload forms: pickers, a file drop and a content
 * textarea.
 *
 * Uploading a file fills the textarea rather than submitting directly. The
 * teacher sees exactly what was extracted and can fix it first - a mangled
 * PDF should never silently become a student's baseline profile. Pasting
 * stays a first-class option, not a fallback.
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
  const extract = useExtractDocument();
  const [extracted, setExtracted] = useState<{
    filename: string;
    words: number;
    format: SourceFormat;
    warnings: string[];
  } | null>(null);

  const {
    register,
    handleSubmit,
    reset,
    getValues,
    setValue,
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
        // Recorded so the engine can ignore typography differences that
        // come from the file format rather than the writer.
        source_format: extracted?.format ?? "paste",
      });
      if (resetOnSuccess) {
        // Keep the pickers where they are - a teacher uploading several
        // papers for one student shouldn't have to reselect every time.
        reset({ ...getValues(), content: "" });
        setExtracted(null);
      }
    } catch {
      // The `error` prop (mutation error) renders the message below.
    }
  };

  async function handleFile(file: File) {
    setExtracted(null);
    try {
      const result = await extract.mutateAsync(file);
      setValue("content", result.text, { shouldValidate: true });
      setExtracted({
        filename: result.filename,
        words: result.word_count,
        format: result.source_format,
        warnings: result.warnings,
      });
    } catch {
      // Rendered from `extract.error` below.
    }
  }

  if (students.isPending || subjects.isPending) {
    return (
      <SkeletonGroup className="space-y-4">
        <SkeletonBar className="h-10 w-full" />
        <SkeletonBar className="h-10 w-full" />
        <SkeletonBar className="h-32 w-full" />
      </SkeletonGroup>
    );
  }

  if (students.isError || subjects.isError) {
    return (
      <Alert variant="danger">
        {getApiErrorMessage(students.error ?? subjects.error)}
      </Alert>
    );
  }

  const hasStudents = students.data.length > 0;
  const hasSubjects = subjects.data.length > 0;

  // Without a student and a subject there is nothing valid to submit. Say so
  // with a way forward rather than rendering a form that can only fail.
  if (!hasStudents || !hasSubjects) {
    return (
      <EmptyState
        title={
          !hasStudents && !hasSubjects
            ? "Add a student and a subject first"
            : !hasStudents
              ? "Add a student first"
              : "Add a subject first"
        }
        description="Every paper is filed against one student and one subject."
        actionLabel={!hasStudents ? "Go to students" : "Go to subjects"}
        actionHref={!hasStudents ? "/students" : "/subjects"}
      />
    );
  }

  return (
    <form onSubmit={handleSubmit(submit)} noValidate className="space-y-5">
      <div className="grid gap-4 sm:grid-cols-2">
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
      </div>

      <div className="space-y-2">
        <FileDropzone onFile={handleFile} disabled={extract.isPending} />
        {extract.isPending ? (
          <div className="flex items-center gap-3">
            <Spinner size="sm" />
            <span className="flex-1 text-footnote text-text-muted">
              Reading the document...
            </span>
          </div>
        ) : null}
        {extract.isPending ? <Progress label="Extracting text" /> : null}
        {extract.isError ? (
          <Alert variant="danger">{getApiErrorMessage(extract.error)}</Alert>
        ) : null}
        {extracted ? (
          <Alert variant="success">
            Read {extracted.words.toLocaleString()} words from{" "}
            <span className="font-medium">{extracted.filename}</span>. Check the
            text below before uploading.
            {extracted.warnings.length > 0 ? (
              <ul className="mt-1 list-inside list-disc">
                {extracted.warnings.map((warning) => (
                  <li key={warning}>{warning}</li>
                ))}
              </ul>
            ) : null}
          </Alert>
        ) : null}
      </div>

      <Textarea
        label="Content"
        placeholder="Paste the student's writing here, or drop a file above..."
        hint={contentHint}
        error={errors.content?.message}
        {...register("content", {
          required: "Content is required",
          validate: (value) => value.trim().length > 0 || "Content is required",
        })}
      />

      {error ? <Alert variant="danger">{getApiErrorMessage(error)}</Alert> : null}

      <Button type="submit" disabled={isSubmitting || extract.isPending}>
        {isSubmitting ? (
          <>
            <Spinner size="sm" className="border-white/40 border-t-white" />
            Uploading...
          </>
        ) : (
          submitLabel
        )}
      </Button>
    </form>
  );
}
