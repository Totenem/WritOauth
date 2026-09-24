"use client";

import { Card, PageHeader } from "@/components";
import { AnalysisUploadForm } from "@/features/papers";

export default function AnalyzeUploadPage() {
  return (
    <div>
      <PageHeader
        title="Check a submission"
        description="Compare new work against the student's baseline. Scoring happens immediately and you'll be taken straight to the result."
        alternate={{ href: "/papers/baseline", label: "Add a baseline instead" }}
      />
      <Card>
        <AnalysisUploadForm />
      </Card>
    </div>
  );
}
