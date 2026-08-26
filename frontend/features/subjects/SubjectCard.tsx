"use client";

import Link from "next/link";
import { Button, Card } from "@/components";
import type { Subject } from "@/types";
import { formatDate } from "@/utils/formatters";

interface SubjectCardProps {
  subject: Subject;
  onDelete?: (subject: Subject) => void;
  isDeleting?: boolean;
}

export default function SubjectCard({ subject, onDelete, isDeleting }: SubjectCardProps) {
  return (
    <Card>
      <div className="flex items-center justify-between gap-4">
        <div className="min-w-0">
          <Link
            href={`/subjects/${subject.id}`}
            className="block truncate font-medium text-primary-700 hover:underline"
          >
            {subject.name}
          </Link>
          <p className="mt-0.5 text-xs text-text-subtle">
            Added {formatDate(subject.created_at)}
          </p>
        </div>

        <div className="flex shrink-0 gap-2">
          <Link
            href={`/subjects/${subject.id}`}
            className="inline-flex items-center justify-center rounded-md border border-border-strong bg-white px-3 py-2 text-sm font-medium text-primary-700 transition-colors hover:bg-bg-subtle"
          >
            Edit
          </Link>
          {onDelete ? (
            <Button
              variant="danger"
              disabled={isDeleting}
              onClick={() => onDelete(subject)}
            >
              {isDeleting ? "Deleting..." : "Delete"}
            </Button>
          ) : null}
        </div>
      </div>
    </Card>
  );
}
