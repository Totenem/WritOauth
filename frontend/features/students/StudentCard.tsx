"use client";

import Link from "next/link";
import { Button, Card } from "@/components";
import type { Student } from "@/types";
import { formatDate } from "@/utils/formatters";

interface StudentCardProps {
  student: Student;
  onDelete?: (student: Student) => void;
  isDeleting?: boolean;
}

export default function StudentCard({ student, onDelete, isDeleting }: StudentCardProps) {
  return (
    <Card>
      <div className="flex items-center justify-between gap-4">
        <div className="min-w-0">
          <Link
            href={`/students/${student.id}`}
            className="block truncate font-medium text-primary-700 hover:underline"
          >
            {student.name}
          </Link>
          <p className="mt-0.5 text-xs text-text-subtle">
            Added {formatDate(student.created_at)}
          </p>
        </div>

        <div className="flex shrink-0 gap-2">
          <Link
            href={`/students/${student.id}`}
            className="inline-flex items-center justify-center rounded-md border border-border-strong bg-white px-3 py-2 text-sm font-medium text-primary-700 transition-colors hover:bg-bg-subtle"
          >
            Edit
          </Link>
          {onDelete ? (
            <Button
              variant="danger"
              disabled={isDeleting}
              onClick={() => onDelete(student)}
            >
              {isDeleting ? "Deleting..." : "Delete"}
            </Button>
          ) : null}
        </div>
      </div>
    </Card>
  );
}
