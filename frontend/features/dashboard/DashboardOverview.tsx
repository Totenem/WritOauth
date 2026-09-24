"use client";

import Link from "next/link";

import { Alert, Badge, Card, EmptyState, SkeletonBar, SkeletonGroup } from "@/components";
import { useDashboard } from "@/hooks/useDashboard";
import type { DashboardStats, StudentStat } from "@/types";
import { getApiErrorMessage } from "@/utils/apiError";
import { formatPercentage } from "@/utils/formatters";

export default function DashboardOverview() {
  const { data, isPending, isError, error } = useDashboard();

  if (isPending) return <DashboardSkeleton />;
  if (isError) return <Alert variant="danger">{getApiErrorMessage(error)}</Alert>;

  // A teacher who has just signed up lands here, so the empty case is the
  // first thing a real user ever sees. It gets onboarding, not zeroes.
  if (data.counts.students === 0 && data.counts.subjects === 0) {
    return (
      <EmptyState
        title="Let's get set up"
        description="Add a student and a subject, then give the system a few writing samples you know are theirs. After that you can check any new submission against them."
        actionLabel="Add your first student"
        actionHref="/students"
      />
    );
  }

  return (
    <div className="space-y-5">
      <StatTiles stats={data} />
      <BaselineReadinessCard stats={data} />

      <div className="grid gap-5 lg:grid-cols-2">
        <LeaderboardCard
          title="Needs a closer look"
          subtitle="Students with submissions the engine scored below the threshold."
          rows={data.students_needing_attention}
          emptyMessage="Nothing flagged so far."
        />
        <LeaderboardCard
          title="Consistently themselves"
          subtitle="Students whose submissions have all matched their baseline."
          rows={data.most_consistent_students}
          emptyMessage="No analysed submissions yet."
        />
      </div>

      <ScoreHistogram stats={data} />
      <RecentActivity stats={data} />
    </div>
  );
}

function StatTiles({ stats }: { stats: DashboardStats }) {
  const tiles = [
    { label: "Students", value: stats.counts.students, href: "/students" },
    { label: "Subjects", value: stats.counts.subjects, href: "/subjects" },
    {
      label: "Baseline papers",
      value: stats.counts.baseline_papers,
      href: "/papers/baseline",
    },
    {
      label: "Submissions checked",
      value: stats.counts.analyses,
      href: "/papers/analyze",
    },
  ];

  return (
    <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
      {tiles.map((tile) => (
        <Link
          key={tile.label}
          href={tile.href}
          className="rounded-xl border border-border bg-bg-elevated p-4 shadow-card transition-colors duration-200 ease-apple hover:border-border-strong"
        >
          <p className="text-footnote text-text-muted">{tile.label}</p>
          <p className="mt-1 text-title1 font-semibold tabular-nums text-text">
            {tile.value.toLocaleString()}
          </p>
        </Link>
      ))}
    </div>
  );
}

/**
 * The most actionable card on the page.
 *
 * A submission from a student with no baseline is silently never analysed -
 * nothing else here would surface that.
 */
function BaselineReadinessCard({ stats }: { stats: DashboardStats }) {
  const { ready, no_baseline, needs_more_samples } = stats.baseline_readiness;
  const unchecked = stats.counts.submissions - stats.counts.analyses;

  return (
    <Card
      title="Baseline readiness"
      subtitle="A student with no baseline on file can't be checked at all."
    >
      <div className="grid grid-cols-3 gap-3 text-center">
        <Stat label="Ready" value={ready} tone="success" />
        <Stat label="Need more samples" value={needs_more_samples} tone="warning" />
        <Stat label="No baseline" value={no_baseline} tone="danger" />
      </div>

      {no_baseline > 0 || unchecked > 0 ? (
        <div className="mt-4 space-y-2">
          {no_baseline > 0 ? (
            <Alert variant="warning">
              {no_baseline} {no_baseline === 1 ? "student has" : "students have"} no
              baseline yet.{" "}
              <Link href="/papers/baseline" className="font-medium underline">
                Add baseline papers
              </Link>
            </Alert>
          ) : null}
          {unchecked > 0 ? (
            <Alert variant="warning">
              {unchecked} {unchecked === 1 ? "submission was" : "submissions were"}{" "}
              saved without being analysed, because the student had no baseline at
              the time. Add one, then upload the submission again.
            </Alert>
          ) : null}
        </div>
      ) : null}
    </Card>
  );
}

function Stat({
  label,
  value,
  tone,
}: {
  label: string;
  value: number;
  tone: "success" | "warning" | "danger";
}) {
  const toneClasses = {
    success: "text-success",
    warning: "text-warning",
    danger: "text-danger",
  } as const;

  return (
    <div className="rounded-lg bg-bg-subtle p-3">
      <p className={`text-title2 font-semibold tabular-nums ${toneClasses[tone]}`}>
        {value}
      </p>
      <p className="mt-0.5 text-caption text-text-muted">{label}</p>
    </div>
  );
}

function LeaderboardCard({
  title,
  subtitle,
  rows,
  emptyMessage,
}: {
  title: string;
  subtitle: string;
  rows: StudentStat[];
  emptyMessage: string;
}) {
  return (
    <Card title={title} subtitle={subtitle}>
      {rows.length === 0 ? (
        <p className="text-subhead text-text-muted">{emptyMessage}</p>
      ) : (
        <ul className="divide-y divide-border">
          {rows.map((row) => (
            <li key={row.student_id} className="flex items-center gap-3 py-2.5">
              <Link
                href={`/students/${row.student_id}`}
                className="flex-1 truncate text-subhead font-medium text-text hover:underline"
              >
                {row.name}
              </Link>
              <span className="text-footnote text-text-muted">
                {row.submissions} checked
              </span>
              {row.flagged > 0 ? (
                <Badge label={`${row.flagged} flagged`} variant="warning" />
              ) : row.average_score !== null ? (
                <span className="text-footnote font-medium tabular-nums text-text">
                  {formatPercentage(row.average_score)}
                </span>
              ) : null}
            </li>
          ))}
        </ul>
      )}
    </Card>
  );
}

function ScoreHistogram({ stats }: { stats: DashboardStats }) {
  const buckets = stats.score_distribution;
  const max = Math.max(1, ...buckets.map((bucket) => bucket.count));
  const total = buckets.reduce((sum, bucket) => sum + bucket.count, 0);

  if (total === 0) return null;

  return (
    <Card
      title="Score distribution"
      subtitle={`All ${total} analysed ${
        total === 1 ? "submission" : "submissions"
      }, by consistency score. The flag threshold is ${stats.verdicts.threshold}%.`}
    >
      <div className="flex items-end gap-2" style={{ height: "8rem" }}>
        {buckets.map((bucket) => (
          <div key={bucket.label} className="flex flex-1 flex-col items-center gap-1.5">
            <span className="text-caption tabular-nums text-text-muted">
              {bucket.count || ""}
            </span>
            <div
              className={`w-full rounded-t-md transition-[height] duration-500 ease-apple ${
                bucket.upper < stats.verdicts.threshold
                  ? "bg-warning/70"
                  : "bg-primary-500"
              }`}
              style={{
                height: `${Math.max(bucket.count > 0 ? 4 : 0, (bucket.count / max) * 100)}%`,
              }}
            />
            <span className="text-caption text-text-subtle">{bucket.label}</span>
          </div>
        ))}
      </div>
    </Card>
  );
}

function RecentActivity({ stats }: { stats: DashboardStats }) {
  return (
    <Card
      title="Recent checks"
      subtitle="The engine's verdict and, where recorded, yours."
    >
      {stats.recent_activity.length === 0 ? (
        <p className="text-subhead text-text-muted">
          Nothing checked yet.{" "}
          <Link href="/papers/analyze" className="text-primary-700 hover:underline">
            Check a submission
          </Link>
        </p>
      ) : (
        <ul className="divide-y divide-border">
          {stats.recent_activity.map((item) => (
            <li key={item.analysis_id} className="flex flex-wrap items-center gap-2 py-2.5">
              <Link
                href={`/analysis/${item.analysis_id}`}
                className="min-w-0 flex-1 truncate text-subhead font-medium text-text hover:underline"
              >
                {item.student_name}
              </Link>
              <span className="text-footnote text-text-muted">
                {item.subject_name}
              </span>
              <span className="text-footnote font-medium tabular-nums text-text">
                {formatPercentage(item.consistency_score)}
              </span>
              <Badge
                label={item.flagged ? "Needs review" : "Consistent"}
                variant={item.flagged ? "warning" : "success"}
              />
              {/* The teacher's own decision, shown separately from the
                  engine's - they answer different questions. */}
              {item.teacher_decision ? (
                <Badge
                  label={`You: ${item.teacher_decision}`}
                  variant={item.teacher_decision === "flagged" ? "danger" : "info"}
                />
              ) : null}
            </li>
          ))}
        </ul>
      )}
    </Card>
  );
}

function DashboardSkeleton() {
  return (
    <SkeletonGroup className="space-y-5">
      <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
        {[0, 1, 2, 3].map((tile) => (
          <div
            key={tile}
            className="rounded-xl border border-border bg-bg-elevated p-4"
          >
            <SkeletonBar className="h-3 w-20" />
            <SkeletonBar className="mt-2 h-7 w-12" />
          </div>
        ))}
      </div>
      <div className="rounded-xl border border-border bg-bg-elevated p-5">
        <SkeletonBar className="h-4 w-40" />
        <div className="mt-4 grid grid-cols-3 gap-3">
          {[0, 1, 2].map((stat) => (
            <SkeletonBar key={stat} className="h-16 w-full" />
          ))}
        </div>
      </div>
      <div className="grid gap-5 lg:grid-cols-2">
        {[0, 1].map((card) => (
          <div key={card} className="rounded-xl border border-border bg-bg-elevated p-5">
            <SkeletonBar className="h-4 w-36" />
            <div className="mt-4 space-y-3">
              {[0, 1, 2].map((row) => (
                <SkeletonBar key={row} className="h-4 w-full" />
              ))}
            </div>
          </div>
        ))}
      </div>
    </SkeletonGroup>
  );
}
