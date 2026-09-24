"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { Alert, useToast } from "@/components";
import { useUploadForAnalysis } from "@/hooks/usePapers";
import type { Paper } from "@/types";
import PaperUploadForm from "./PaperUploadForm";

export default function AnalysisUploadForm() {
  const router = useRouter();
  const uploadForAnalysis = useUploadForAnalysis();
  const { toast } = useToast();
  // Only set when the upload succeeded but produced no analysis, i.e. the
  // student has no baseline yet. A successful analysis navigates away.
  const [unanalysed, setUnanalysed] = useState<Paper | null>(null);

  return (
    <div className="space-y-4">
      {unanalysed ? (
        <Alert variant="warning" title="Saved, but not analysed">
          There&apos;s no baseline on file for this student yet, so there was
          nothing to compare the submission against.{" "}
          <Link href="/papers/baseline" className="font-medium underline">
            Add a baseline first
          </Link>
          , then upload this submission again.{" "}
          <Link
            href={`/papers/${unanalysed.id}`}
            className="font-medium underline"
          >
            View paper
          </Link>
        </Alert>
      ) : null}

      <PaperUploadForm
        submitLabel="Check this submission"
        contentHint="This is scored against the student's baseline profile as soon as it's uploaded."
        onSubmit={async (values) => {
          setUnanalysed(null);
          const paper = await uploadForAnalysis.mutateAsync(values);
          if (paper.analysis_id != null) {
            toast("Submission analysed");
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
