"use client";

import Link from "next/link";

import { Alert, Badge, Card, EmptyState, SkeletonBar, SkeletonGroup } from "@/components";
import { useAnalysis } from "@/hooks/useAnalysis";
import type { Reliability } from "@/types";
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
    return <AnalysisSkeleton />;
  }

  if (isError) {
    return <NotFound message={getApiErrorMessage(error)} />;
  }

  const { breakdown } = analysis;
  const caveats = reliabilityCaveats(breakdown.reliability);

  return (
    <div className="space-y-5">
      <Card>
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <p className="text-footnote text-text-muted">Consistency with baseline</p>
            <p className="mt-0.5 text-largeTitle font-semibold tabular-nums text-text">
              {formatPercentage(analysis.consistency_score)}
            </p>
            <div className="mt-2">
              {/*
                `flagged` is computed server-side against the engine's own
                threshold. The client never infers a verdict by comparing a
                score to a number it holds itself.
              */}
              <Badge
                label={analysis.flagged ? "Needs review" : "Consistent"}
                variant={analysis.flagged ? "warning" : "success"}
              />
            </div>
          </div>
          <Link
            href={`/papers/${analysis.paper_id}`}
            className="text-subhead text-primary-700 hover:underline"
          >
            View submitted paper &rarr;
          </Link>
        </div>

        <p className="mt-4 border-t border-border pt-4 text-subhead leading-relaxed text-text">
          {analysis.explanation}
        </p>
      </Card>

      {caveats.length > 0 ? (
        <Alert variant="warning" title="Read this score with care">
          <ul className="list-inside list-disc space-y-0.5">
            {caveats.map((caveat) => (
              <li key={caveat}>{caveat}</li>
            ))}
          </ul>
        </Alert>
      ) : null}

      <Card>
        <ScoreBreakdown breakdown={breakdown} />
      </Card>

      <Card
        title="Baseline strength"
        subtitle="How much of this student's own writing the comparison rests on. This measures the evidence behind the result, not how suspicious the submission is."
      >
        <p className="text-title1 font-semibold tabular-nums text-text">
          {formatScore(analysis.confidence_level)}
        </p>
        <p className="mt-1 text-footnote text-text-muted">
          {breakdown.reliability.n_baseline_papers}{" "}
          {breakdown.reliability.n_baseline_papers === 1 ? "paper" : "papers"} on
          file, {breakdown.reliability.total_baseline_words.toLocaleString()} words.
        </p>
        {analysis.confidence_level < 1 ? (
          <p className="mt-3 text-footnote text-text-muted">
            <Link
              href="/papers/baseline"
              className="text-primary-700 hover:underline"
            >
              Add more baseline papers
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

/**
 * Turns the reliability block into plain warnings.
 *
 * A 92% on a 120-word paragraph should not look as solid as a 92% on a
 * 900-word essay, and nothing else on the page makes that difference visible.
 */
function reliabilityCaveats(reliability: Reliability): string[] {
  const caveats: string[] = [];

  if (reliability.n_baseline_papers < 3) {
    caveats.push(
      `This student has only ${reliability.n_baseline_papers} baseline ${
        reliability.n_baseline_papers === 1 ? "paper" : "papers"
      } on file, so the comparison rests on a thin profile.`
    );
  }
  if (reliability.submission_word_count < 150) {
    caveats.push(
      `At ${reliability.submission_word_count} words this submission is short, which makes every measurement noisier.`
    );
  }
  if (!reliability.paragraphs_reliable) {
    caveats.push(
      "The submission has no paragraph breaks, so paragraph structure could not be compared."
    );
  }
  return caveats;
}

function AnalysisSkeleton() {
  return (
    <div className="space-y-5">
      <Card>
        <SkeletonGroup className="space-y-3">
          <SkeletonBar className="h-3 w-40" />
          <SkeletonBar className="h-9 w-28" />
          <SkeletonBar className="h-5 w-24 rounded-full" />
          <SkeletonBar className="h-16 w-full" />
        </SkeletonGroup>
      </Card>
      <Card>
        <SkeletonGroup className="space-y-4">
          <SkeletonBar className="h-4 w-48" />
          {[0, 1, 2, 3, 4, 5].map((row) => (
            <div key={row} className="space-y-1.5">
              <SkeletonBar className="h-3 w-32" />
              <SkeletonBar className="h-2 w-full" />
            </div>
          ))}
        </SkeletonGroup>
      </Card>
    </div>
  );
}

function NotFound({ message }: { message?: string }) {
  return (
    <EmptyState
      title="Analysis not found"
      description={message ?? "That analysis does not exist."}
      actionLabel="Check a submission"
      actionHref="/papers/analyze"
    />
  );
}
