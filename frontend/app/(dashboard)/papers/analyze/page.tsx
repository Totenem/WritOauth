"use client";

import Link from "next/link";
import { Card } from "@/components";
import { AnalysisUploadForm } from "@/features/papers";

export default function AnalyzeUploadPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-text">Upload a submission</h1>
        <p className="mt-1 text-sm text-text-muted">
          The submission is scored against the student&apos;s baseline profile as soon
          as it&apos;s uploaded, and you&apos;ll be taken straight to the results.{" "}
          <Link href="/papers/baseline" className="text-primary-700 hover:underline">
            Upload a baseline paper instead
          </Link>
        </p>
      </div>

      <Card>
        <AnalysisUploadForm />
      </Card>
    </div>
  );
}
