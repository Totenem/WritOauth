"use client";

import Link from "next/link";
import { Badge, Card, Spinner } from "@/components";
import { usePaper } from "@/hooks/usePapers";
import { useStudents } from "@/hooks/useStudents";
import { useSubjects } from "@/hooks/useSubjects";
import { getApiErrorMessage } from "@/utils/apiError";
import { formatDate } from "@/utils/formatters";

export default function PaperDetail({ id }: { id: number }) {
  const { data: paper, isPending, isError, error } = usePaper(id);
  // GET /api/papers/{id} returns ids, not names, and there's no endpoint that
  // expands them — so resolve against the rosters already in the query cache.
  const students = useStudents();
  const subjects = useSubjects();

  if (!Number.isFinite(id)) {
    return <NotFound />;
  }

  if (isPending) {
    return (
      <div className="flex justify-center py-8">
        <Spinner />
      </div>
    );
  }

  if (isError) {
    return <NotFound message={getApiErrorMessage(error)} />;
  }

  const studentName = students.data?.find((s) => s.id === paper.student_id)?.name;
  const subjectName = subjects.data?.find((s) => s.id === paper.subject_id)?.name;
  const isBaseline = paper.type === "baseline";

  return (
    <Card>
      <div className="flex items-center gap-3">
        <h2 className="text-lg font-medium text-text">Paper #{paper.id}</h2>
        <Badge
          label={isBaseline ? "Baseline" : "Submission"}
          variant={isBaseline ? "info" : "warning"}
        />
      </div>

      <dl className="mt-4 space-y-2 text-sm">
        <div className="flex gap-2">
          <dt className="w-24 shrink-0 text-text-subtle">Student</dt>
          <dd className="text-text">
            <Link
              href={`/students/${paper.student_id}`}
              className="text-primary-700 hover:underline"
            >
              {studentName ?? `Student #${paper.student_id}`}
            </Link>
          </dd>
        </div>
        <div className="flex gap-2">
          <dt className="w-24 shrink-0 text-text-subtle">Subject</dt>
          <dd className="text-text">
            <Link
              href={`/subjects/${paper.subject_id}`}
              className="text-primary-700 hover:underline"
            >
              {subjectName ?? `Subject #${paper.subject_id}`}
            </Link>
          </dd>
        </div>
        <div className="flex gap-2">
          <dt className="w-24 shrink-0 text-text-subtle">Uploaded</dt>
          <dd className="text-text">{formatDate(paper.created_at)}</dd>
        </div>
      </dl>

      <div className="mt-4 border-t border-border pt-4 text-sm">
        {isBaseline ? (
          <p className="text-text-muted">
            Baseline papers build the student&apos;s writing profile; they aren&apos;t
            scored themselves.
          </p>
        ) : paper.analysis_id != null ? (
          <Link
            href={`/analysis/${paper.analysis_id}`}
            className="font-medium text-primary-700 hover:underline"
          >
            View analysis results &rarr;
          </Link>
        ) : (
          <p className="text-text-muted">
            No analysis for this submission — there was no baseline on file for this
            student when it was uploaded.{" "}
            <Link href="/papers/baseline" className="text-primary-700 hover:underline">
              Upload a baseline
            </Link>
            , then re-upload the submission.
          </p>
        )}
      </div>
    </Card>
  );
}

function NotFound({ message }: { message?: string }) {
  return (
    <Card>
      <h2 className="text-lg font-medium text-text">Paper not found</h2>
      <p className="mt-1 text-sm text-text-muted">
        {message ?? "That paper does not exist."}
      </p>
    </Card>
  );
}
