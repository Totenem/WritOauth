"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { EmptyState, SkeletonBar, SkeletonGroup, useToast } from "@/components";
import { ArrowLeftIcon, CopyIcon, SettingsIcon } from "@/components/icons";
import { BatchUpload, CourseRoster, CourseSettingsModal } from "@/features/subjects";
import { useSubject } from "@/hooks/useSubjects";
import { getApiErrorMessage } from "@/utils/apiError";

export default function SubjectDetailPage({ params }: { params: { id: string } }) {
  const router = useRouter();
  const subjectId = Number(params.id);
  const { data: subject, isPending, isError, error } = useSubject(subjectId);
  const [managing, setManaging] = useState(false);
  const { toast } = useToast();

  if (!Number.isFinite(subjectId)) return <NotFound />;

  if (isPending) {
    return (
      <SkeletonGroup className="space-y-6">
        <SkeletonBar className="h-28 w-full rounded-2xl" />
        <SkeletonBar className="h-48 w-full rounded-2xl" />
      </SkeletonGroup>
    );
  }

  // Another teacher's course also lands here: the backend answers 404 rather
  // than 403 on purpose, so it can't be told apart from one that never existed.
  if (isError) return <NotFound message={getApiErrorMessage(error)} />;

  const copyCode = async () => {
    try {
      await navigator.clipboard.writeText(subject.course_code);
      toast(`Copied ${subject.course_code}`);
    } catch {
      toast("Couldn't copy - select the code and copy it manually", "error");
    }
  };

  return (
    <div className="space-y-6">
      <Link
        href="/subjects"
        className="inline-flex items-center gap-1 text-footnote font-medium text-primary-700 hover:underline"
      >
        <ArrowLeftIcon className="h-3.5 w-3.5" />
        All courses
      </Link>

      <section className="flex flex-wrap items-start justify-between gap-4 rounded-2xl border border-border bg-bg-elevated p-5 shadow-card sm:p-6">
        <div className="min-w-0">
          <div className="flex items-center gap-2">
            <span className="select-all font-mono text-footnote font-semibold tracking-wide text-accent">
              {subject.course_code}
            </span>
            <button
              type="button"
              onClick={copyCode}
              aria-label="Copy course code"
              className="rounded-md p-1 text-text-subtle hover:bg-bg-subtle hover:text-text"
            >
              <CopyIcon className="h-3.5 w-3.5" />
            </button>
          </div>
          <h1 className="mt-1 text-title2 font-extrabold tracking-tight text-text">{subject.name}</h1>
          <p className="mt-1 text-footnote text-text-muted">
            {subject.student_count} active {subject.student_count === 1 ? "student" : "students"} ·{" "}
            {subject.baseline_ready_count} baseline-locked
          </p>
        </div>
        <button
          type="button"
          onClick={() => setManaging(true)}
          className="inline-flex items-center gap-1.5 rounded-lg border border-border-strong bg-bg px-3.5 py-2 text-footnote font-semibold text-text transition-colors duration-200 ease-apple hover:border-primary-400 hover:text-primary-700"
        >
          <SettingsIcon className="h-4 w-4" />
          Course settings
        </button>
      </section>

      <BatchUpload subject={subject} />
      <CourseRoster subjectId={subject.id} />

      <CourseSettingsModal
        subject={managing ? subject : null}
        onClose={() => setManaging(false)}
        onDeleted={() => router.push("/subjects")}
      />
    </div>
  );
}

function NotFound({ message }: { message?: string }) {
  return (
    <EmptyState
      title="Course not found"
      description={message ?? "That course doesn't exist, or it belongs to another teacher."}
      actionLabel="Back to courses"
      actionHref="/subjects"
    />
  );
}
