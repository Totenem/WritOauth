"use client";

import Link from "next/link";
import { useState } from "react";

import { Alert, useToast } from "@/components";
import { useUploadBaseline } from "@/hooks/usePapers";
import type { Paper } from "@/types";
import PaperUploadForm from "./PaperUploadForm";

export default function BaselineUploadForm() {
  const uploadBaseline = useUploadBaseline();
  const { toast } = useToast();
  const [uploaded, setUploaded] = useState<Paper | null>(null);

  return (
    <div className="space-y-4">
      {uploaded ? (
        <Alert variant="success">
          Baseline added. This student&apos;s writing profile has been updated.{" "}
          <Link href={`/papers/${uploaded.id}`} className="font-medium underline">
            View paper
          </Link>
        </Alert>
      ) : null}

      <PaperUploadForm
        submitLabel="Add baseline"
        contentHint="Use writing you're confident the student produced themselves. Three or more samples, on different topics, give the strongest profile."
        onSubmit={async (values) => {
          const paper = await uploadBaseline.mutateAsync(values);
          setUploaded(paper);
          toast("Baseline added");
          return paper;
        }}
        isSubmitting={uploadBaseline.isPending}
        error={uploadBaseline.error}
        resetOnSuccess
      />
    </div>
  );
}
