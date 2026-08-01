"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useUploadForAnalysis } from "@/hooks/usePapers";
import type { Paper } from "@/types";
import PaperUploadForm from "./PaperUploadForm";

export default function AnalysisUploadForm() {
  const router = useRouter();
  const uploadForAnalysis = useUploadForAnalysis();
  // Only set when the upload succeeded but produced no analysis, i.e. the
  // student has no baseline yet. A successful analysis navigates away instead.
  const [unanalysed, setUnanalysed] = useState<Paper | null>(null);

  return (
    <div className="space-y-4">
      {unanalysed ? (
        <div
          role="status"
          className="rounded-md border border-border bg-warning-bg p-3 text-sm text-warning"
        >
          Submission saved, but it couldn&apos;t be analysed: there&apos;s no baseline
          on file yet for this student.{" "}
          <Link href="/papers/baseline" className="font-medium underline">
            Upload a baseline paper first
          </Link>
          , then re-upload this submission.{" "}
          <Link href={`/papers/${unanalysed.id}`} className="font-medium underline">
            View paper
          </Link>
        </div>
      ) : null}

      <PaperUploadForm
        submitLabel="Upload for analysis"
        contentHint="This will be scored against the student's baseline writing profile."
        onSubmit={async (values) => {
          setUnanalysed(null);
          const paper = await uploadForAnalysis.mutateAsync(values);
          if (paper.analysis_id != null) {
            router.push(`/analysis/${paper.analysis_id}`);
          } else {
            setUnanalysed(paper);
          }
          return paper;
        }}
        isSubmitting={uploadForAnalysis.isPending}
        error={uploadForAnalysis.error}
      />
    </div>
  );
}
