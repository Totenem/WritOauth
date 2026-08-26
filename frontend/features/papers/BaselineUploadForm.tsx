"use client";

import { useState } from "react";
import Link from "next/link";
import { useUploadBaseline } from "@/hooks/usePapers";
import type { Paper } from "@/types";
import PaperUploadForm from "./PaperUploadForm";

export default function BaselineUploadForm() {
  const uploadBaseline = useUploadBaseline();
  const [uploaded, setUploaded] = useState<Paper | null>(null);

  return (
    <div className="space-y-4">
      {uploaded ? (
        <div
          role="status"
          className="rounded-md border border-border bg-success-bg p-3 text-sm text-success"
        >
          Baseline uploaded. This student&apos;s writing profile has been updated.{" "}
          <Link href={`/papers/${uploaded.id}`} className="font-medium underline">
            View paper
          </Link>
        </div>
      ) : null}

      <PaperUploadForm
        submitLabel="Upload baseline"
        contentHint="Use a piece of writing you're confident the student wrote themselves. Longer samples give a better profile."
        onSubmit={async (values) => {
          const paper = await uploadBaseline.mutateAsync(values);
          setUploaded(paper);
          return paper;
        }}
        isSubmitting={uploadBaseline.isPending}
        error={uploadBaseline.error}
        resetOnSuccess
      />
    </div>
  );
}
