"use client";

import Link from "next/link";
import { Button, Card } from "@/components";
import type { Student } from "@/types";

interface StudentCardProps {
  student: Student;
  onDelete?: (student: Student) => void;
  isDeleting?: boolean;
}

export default function StudentCard({ student, onDelete, isDeleting }: StudentCardProps) {
  return (
    <Card>
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div className="min-w-0">
          <Link
            href={`/students/${student.id}`}
            className="block truncate font-semibold text-text hover:text-primary-700 hover:underline"
          >
            {student.name}
          </Link>
          {student.email ? (
            <p className="mt-0.5 truncate text-footnote text-text-muted">{student.email}</p>
          ) : null}
          <ul className="mt-2 flex flex-wrap gap-1.5" aria-label="Enrolled courses">
            {student.subjects.length === 0 ? (
              <li className="text-caption text-warning">Not enrolled in any course</li>
            ) : (
              student.subjects.map((subject) => (
                <li key={subject.id}>
                  <Link
                    href={`/subjects/${subject.id}`}
                    className="inline-flex items-center gap-1 rounded-md border border-border bg-bg-subtle px-2 py-0.5 text-caption text-text-muted hover:border-primary-300 hover:text-primary-700"
                  >
                    {subject.name}
                    <span className="font-mono text-accent">{subject.course_code}</span>
                  </Link>
                </li>
              ))
            )}
          </ul>
        </div>

        <div className="flex shrink-0 gap-2">
          <Link
            href={`/students/${student.id}`}
            className="inline-flex items-center justify-center rounded-lg border border-border-strong bg-bg px-3 py-2 text-sm font-medium text-primary-700 transition-colors hover:bg-bg-subtle"
          >
            Edit
          </Link>
          {onDelete ? (
            <Button variant="danger" disabled={isDeleting} onClick={() => onDelete(student)}>
              {isDeleting ? "Deleting..." : "Delete"}
            </Button>
          ) : null}
        </div>
      </div>
    </Card>
  );
}
