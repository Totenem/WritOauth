"use client";

import Link from "next/link";
import { AnalysisReport } from "@/features/analysis";

export default function AnalysisReportPage({ params }: { params: { id: string } }) {
  return (
    <div className="space-y-6">
      <div>
        <Link href="/papers/analyze" className="text-sm text-primary-700 hover:underline">
          &larr; Upload another submission
        </Link>
        <h1 className="mt-2 text-2xl font-semibold text-text">Analysis result</h1>
      </div>

      <AnalysisReport id={Number(params.id)} />
    </div>
  );
}
