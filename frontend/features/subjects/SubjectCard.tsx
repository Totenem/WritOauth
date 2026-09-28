"use client";

import Link from "next/link";
import { SettingsIcon } from "@/components/icons";
import type { Subject } from "@/types";

interface SubjectCardProps {
  subject: Subject;
  onManage?: (subject: Subject) => void;
}

export default function SubjectCard({ subject, onManage }: SubjectCardProps) {
  const { student_count: total, baseline_ready_count: ready } = subject;
  const percent = total > 0 ? Math.round((ready / total) * 100) : 0;

  return (
    <article className="flex h-full flex-col rounded-2xl border border-border bg-bg-elevated p-5 shadow-card transition-colors duration-200 ease-apple hover:border-border-strong">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <p className="font-mono text-caption font-semibold tracking-wide text-accent">
            {subject.course_code}
          </p>
          <h3 className="mt-1 truncate text-headline font-bold text-text">
            <Link href={`/subjects/${subject.id}`} className="hover:underline">
              {subject.name}
            </Link>
          </h3>
        </div>
        <span
          className="flex h-8 min-w-8 shrink-0 items-center justify-center rounded-lg border border-border bg-bg px-2 text-footnote font-bold tabular-nums text-text"
          title="Active students enrolled"
          aria-label={`${total} ${total === 1 ? "student" : "students"} enrolled`}
        >
          {total}
        </span>
      </div>

      <div className="mt-4">
        <div className="flex items-center justify-between text-caption">
          <span className="text-text-muted">Baseline Locked Students:</span>
          <span className="font-bold tabular-nums text-text">
            {ready} / {total}
          </span>
        </div>
        <div
          role="progressbar"
          aria-label="Students with a complete baseline"
          aria-valuemin={0}
          aria-valuemax={total}
          aria-valuenow={ready}
          className="mt-1.5 h-1.5 overflow-hidden rounded-full bg-bg-muted"
        >
          <div
            className="h-full rounded-full bg-primary-500 transition-[width] duration-500 ease-apple"
            style={{ width: `${percent}%` }}
          />
        </div>
      </div>

      <div className="mt-auto flex gap-2 pt-5">
        <Link
          href={`/subjects/${subject.id}`}
          className="flex h-9 flex-1 items-center justify-center rounded-lg border border-border-strong bg-bg text-footnote font-semibold text-text transition-colors duration-200 ease-apple hover:border-primary-400 hover:text-primary-700"
        >
          View Roster
        </Link>
        {onManage ? (
          <button
            type="button"
            onClick={() => onManage(subject)}
            aria-label={`Manage ${subject.name}`}
            className="flex h-9 w-9 items-center justify-center rounded-lg border border-border-strong bg-bg text-text-muted transition-colors duration-200 ease-apple hover:border-primary-400 hover:text-primary-700"
          >
            <SettingsIcon className="h-4 w-4" />
          </button>
        ) : null}
      </div>
    </article>
  );
}
