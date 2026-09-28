"use client";

import { Alert, FileDropzone } from "@/components";
import { DownloadIcon, UploadIcon } from "@/components/icons";
import { useBatchUploadStudents } from "@/hooks/useSubjects";
import type { Subject } from "@/types";
import { getApiErrorMessage } from "@/utils/apiError";

/** Must match BATCH_HEADERS in backend/application/services/subject_service.py. */
export const TEMPLATE_HEADERS = ["Subject Code", "Last Name", "First Name", "Email", "Status"];

function downloadTemplate(courseCode: string) {
  const csv = `${TEMPLATE_HEADERS.join(",")}\r\n`;
  const url = URL.createObjectURL(new Blob([csv], { type: "text/csv;charset=utf-8" }));
  const link = document.createElement("a");
  link.href = url;
  link.download = `${courseCode}-roster-template.csv`;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
}

export default function BatchUpload({ subject }: { subject: Subject }) {
  const upload = useBatchUploadStudents(subject.id);
  const result = upload.data;

  return (
    <section className="rounded-2xl border border-border bg-bg-elevated p-5 shadow-card sm:p-6">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h2 className="flex items-center gap-2 text-headline font-bold text-text">
            <UploadIcon className="h-5 w-5 text-primary-600" />
            Batch enroll students
          </h2>
          <p className="mt-1 max-w-xl text-footnote text-text-muted">
            Download the template, fill in one student per row, and put{" "}
            <span className="font-mono font-semibold text-accent">{subject.course_code}</span> in
            the Subject Code column. Status is <em>active</em> or <em>inactive</em> (blank means
            active).
          </p>
        </div>
        <button
          type="button"
          onClick={() => downloadTemplate(subject.course_code)}
          className="inline-flex items-center gap-1.5 rounded-lg border border-border-strong bg-bg px-3.5 py-2 text-footnote font-semibold text-text transition-colors duration-200 ease-apple hover:border-primary-400 hover:text-primary-700"
        >
          <DownloadIcon className="h-4 w-4" />
          Download Template
        </button>
      </div>

      <div className="mt-4">
        <FileDropzone
          accept=".csv"
          disabled={upload.isPending}
          hint={upload.isPending ? "Uploading…" : "Drop the filled-in CSV here, or click to choose it"}
          onFile={(file) => upload.mutate(file)}
        />
      </div>

      <div aria-live="polite" className="mt-4 space-y-2 empty:hidden">
        {upload.isError ? (
          <Alert variant="danger">{getApiErrorMessage(upload.error)}</Alert>
        ) : null}
        {result ? (
          <Alert variant={result.created_count > 0 ? "success" : "warning"}>
            Enrolled {result.created_count} {result.created_count === 1 ? "student" : "students"}
            {result.skipped.length > 0
              ? `, skipped ${result.skipped.length} ${result.skipped.length === 1 ? "row" : "rows"}.`
              : "."}
          </Alert>
        ) : null}
        {result && result.skipped.length > 0 ? (
          <ul className="max-h-48 space-y-1 overflow-y-auto rounded-xl border border-border bg-bg-subtle p-3 text-footnote">
            {result.skipped.map((skip) => (
              <li key={skip.row} className="flex gap-2">
                <span className="shrink-0 font-semibold tabular-nums text-text">Row {skip.row}</span>
                <span className="text-text-muted">{skip.reason}</span>
              </li>
            ))}
          </ul>
        ) : null}
      </div>
    </section>
  );
}
