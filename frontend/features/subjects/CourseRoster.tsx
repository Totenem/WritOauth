"use client";

import Link from "next/link";

import { Alert, SkeletonBar, SkeletonGroup } from "@/components";
import { UsersIcon } from "@/components/icons";
import { useSubjectRoster } from "@/hooks/useSubjects";
import { getApiErrorMessage } from "@/utils/apiError";

const MIN_BASELINE_PAPERS = 3;

export default function CourseRoster({ subjectId }: { subjectId: number }) {
  const { data: roster, isPending, isError, error } = useSubjectRoster(subjectId);

  return (
    <section className="rounded-2xl border border-border bg-bg-elevated shadow-card">
      <div className="px-5 pt-5 sm:px-6">
        <h2 className="flex items-center gap-2 text-headline font-bold text-text">
          <UsersIcon className="h-5 w-5 text-primary-600" />
          Course roster
        </h2>
        <p className="mt-1 text-footnote text-text-muted">
          A student is baseline-locked once they have {MIN_BASELINE_PAPERS} verified writing samples.
        </p>
      </div>

      {isPending ? (
        <SkeletonGroup className="space-y-3 p-5 sm:p-6">
          {[0, 1, 2].map((row) => (
            <SkeletonBar key={row} className="h-10 w-full" />
          ))}
        </SkeletonGroup>
      ) : isError ? (
        <div className="p-5 sm:p-6">
          <Alert variant="danger">{getApiErrorMessage(error)}</Alert>
        </div>
      ) : roster.students.length === 0 ? (
        <p className="px-5 pb-6 pt-4 text-subhead text-text-muted sm:px-6">
          No students enrolled yet. Use the template above to add your class in one go.
        </p>
      ) : (
        <div className="mt-4 overflow-x-auto px-5 pb-5 sm:px-6">
          <table className="w-full min-w-[40rem] text-left">
            <thead>
              <tr className="bg-bg-subtle text-caption font-semibold uppercase tracking-wider text-text-muted">
                <th scope="col" className="rounded-l-lg px-4 py-3">Student</th>
                <th scope="col" className="px-4 py-3">Email</th>
                <th scope="col" className="px-4 py-3">Status</th>
                <th scope="col" className="rounded-r-lg px-4 py-3">Baseline</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {roster.students.map((student) => (
                <tr key={student.id} className="text-footnote">
                  <td className="px-4 py-3.5">
                    <Link
                      href={`/students/${student.id}`}
                      className="font-semibold text-text hover:text-primary-700 hover:underline"
                    >
                      {student.name}
                    </Link>
                  </td>
                  <td className="px-4 py-3.5 text-text-muted">{student.email ?? "—"}</td>
                  <td className="px-4 py-3.5">
                    <span
                      className={`inline-flex rounded-full border px-2.5 py-0.5 text-caption font-semibold capitalize ${
                        student.status === "active"
                          ? "border-success/40 bg-success-bg text-success"
                          : "border-border-strong bg-bg-muted text-text-muted"
                      }`}
                    >
                      {student.status}
                    </span>
                  </td>
                  <td className="px-4 py-3.5">
                    <span
                      className={`font-semibold tabular-nums ${
                        student.baseline_ready ? "text-success" : "text-warning"
                      }`}
                    >
                      {Math.min(student.baseline_paper_count, MIN_BASELINE_PAPERS)} / {MIN_BASELINE_PAPERS}
                    </span>
                    <span className="ml-2 text-caption text-text-subtle">
                      {student.baseline_ready ? "Locked" : "Collecting"}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}
