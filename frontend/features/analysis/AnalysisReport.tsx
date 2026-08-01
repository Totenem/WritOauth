"use client";

import Link from "next/link";
import { Card, Spinner } from "@/components";
import { useAnalysis } from "@/hooks/useAnalysis";
import { getApiErrorMessage } from "@/utils/apiError";
import { formatPercentage, formatScore } from "@/utils/formatters";
import FeedbackForm from "./FeedbackForm";
import ScoreBreakdown from "./ScoreBreakdown";

export default function AnalysisReport({ id }: { id: number }) {
  const { data: analysis, isPending, isError, error } = useAnalysis(id);

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

  return (
    <div className="space-y-6">
      <Card>
        <div className="flex flex-wrap items-baseline justify-between gap-4">
          <div>
            <p className="text-sm text-text-muted">Consistency with baseline</p>
            <p className="text-4xl font-semibold tabular-nums text-text">
              {formatPercentage(analysis.consistency_score)}
            </p>
          </div>
          <Link
            href={`/papers/${analysis.paper_id}`}
            className="text-sm text-primary-700 hover:underline"
          >
            View submitted paper &rarr;
          </Link>
        </div>

        {/*
          The explanation is the backend's own plain-language verdict, and it
          already states the flag threshold it used. It's shown as the primary
          reading of the result rather than a badge computed here, because the
          API returns no flagged/genuine field and no threshold field — only
          this sentence. Recomputing a verdict client-side would mean hardcoding
          a threshold the backend might not be using.
        */}
        <p className="mt-4 border-t border-border pt-4 text-sm leading-relaxed text-text">
          {analysis.explanation}
        </p>
      </Card>

      <Card>
        <ScoreBreakdown breakdown={analysis.breakdown} />
      </Card>

      <Card>
        <h2 className="text-lg font-medium text-text">Baseline strength</h2>
        <p className="mt-1 text-sm text-text-muted">
          How much baseline writing this student has on file. This is a measure of
          the evidence behind the comparison, not of how suspicious the submission
          is — it reaches full strength at three baseline papers.
        </p>
        <p className="mt-2 text-2xl font-semibold tabular-nums text-text">
          {formatScore(analysis.confidence_level)}
        </p>
        {analysis.confidence_level < 1 ? (
          <p className="mt-2 text-sm text-text-muted">
            <Link href="/papers/baseline" className="text-primary-700 hover:underline">
              Upload more baseline papers
            </Link>{" "}
            for this student to make future comparisons more reliable.
          </p>
        ) : null}
      </Card>

      <Card>
        <FeedbackForm analysisId={analysis.id} />
      </Card>
    </div>
  );
}

function NotFound({ message }: { message?: string }) {
  return (
    <Card>
      <h2 className="text-lg font-medium text-text">Analysis not found</h2>
      <p className="mt-1 text-sm text-text-muted">
        {message ?? "That analysis does not exist."}
      </p>
    </Card>
  );
}
