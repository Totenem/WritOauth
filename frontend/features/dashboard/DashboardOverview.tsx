"use client";

import Link from "next/link";

import { Alert, EmptyState, SkeletonBar, SkeletonGroup } from "@/components";
import {
  AlertTriangleIcon,
  BoltIcon,
  CheckCircleIcon,
  ClockIcon,
  ShieldIcon,
  TargetIcon,
  UserCheckIcon,
} from "@/components/icons";
import { useDashboard } from "@/hooks/useDashboard";
import type { DashboardStats, RecentAnalysis, StudentStat } from "@/types";
import { getApiErrorMessage } from "@/utils/apiError";
import { formatDate, formatPercentage } from "@/utils/formatters";

type Tone = "primary" | "success" | "warning" | "accent";

const toneText: Record<Tone, string> = {
  primary: "text-text",
  success: "text-success",
  warning: "text-warning",
  accent: "text-accent",
};

const toneIcon: Record<Tone, string> = {
  primary: "border-primary-200 bg-primary-50 text-primary-700",
  success: "border-success/30 bg-success-bg text-success",
  warning: "border-warning/30 bg-warning-bg text-warning",
  accent: "border-accent/30 bg-accent-soft/20 text-accent",
};

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
    <div className="space-y-6">
      <CommandCenter stats={data} />
      <KpiTiles stats={data} />
      <BaselineWarnings stats={data} />
      <SubmissionsQueue stats={data} />

      <div className="grid gap-6 lg:grid-cols-2">
        <BaselineReadiness stats={data} />
        <ScoreHistogram stats={data} />
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <Leaderboard
          title="Needs a closer look"
          subtitle="Students with submissions the engine scored below the threshold."
          rows={data.students_needing_attention}
          emptyMessage="Nothing flagged so far."
        />
        <Leaderboard
          title="Consistently themselves"
          subtitle="Students whose submissions have all matched their baseline."
          rows={data.most_consistent_students}
          emptyMessage="No analysed submissions yet."
        />
      </div>
    </div>
  );
}

function Panel({
  children,
  className = "",
}: {
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <section className={`rounded-2xl border border-border bg-bg-elevated shadow-card ${className}`}>
      {children}
    </section>
  );
}

function PanelHeader({
  title,
  subtitle,
  icon,
  action,
}: {
  title: string;
  subtitle?: string;
  icon?: React.ReactNode;
  action?: React.ReactNode;
}) {
  return (
    <div className="flex flex-wrap items-start justify-between gap-3 px-5 pt-5">
      <div>
        <h2 className="flex items-center gap-2 text-headline font-bold text-text">
          {icon}
          {title}
        </h2>
        {subtitle ? <p className="mt-0.5 text-footnote text-text-muted">{subtitle}</p> : null}
      </div>
      {action}
    </div>
  );
}

function CommandCenter({ stats }: { stats: DashboardStats }) {
  const { students, subjects } = stats.counts;
  const coverage = students > 0 ? (stats.baseline_readiness.ready / students) * 100 : 0;

  return (
    <Panel className="relative overflow-hidden bg-gradient-to-br from-bg-elevated via-bg-elevated to-primary-50 p-6 sm:p-8">
      <div className="flex flex-col gap-6 lg:flex-row lg:items-center lg:justify-between">
        <div className="max-w-2xl">
          <span className="inline-flex items-center gap-1.5 rounded-full border border-accent/40 bg-accent-soft/15 px-3 py-1 text-caption font-semibold text-accent">
            <ShieldIcon className="h-3.5 w-3.5" />
            Baseline protection active across {subjects} {subjects === 1 ? "course" : "courses"}
          </span>
          <h1 className="mt-4 text-[1.75rem] font-extrabold leading-tight tracking-tight text-text sm:text-[2rem]">
            Educator Command Center
          </h1>
          <p className="mt-2 text-subhead text-text-muted">
            WritOath compares each submission against the student&apos;s{" "}
            <strong className="font-semibold text-text">3 verified baseline papers</strong>. Protect
            honest student writing without relying on generic, error-prone AI detectors.
          </p>
        </div>

        <dl className="grid shrink-0 grid-cols-3 divide-x divide-border rounded-2xl border border-border bg-bg/60 py-4 text-center">
          <HeroStat label="Students enrolled" value={students.toLocaleString()} />
          <HeroStat label="Baseline coverage" value={`${coverage.toFixed(1)}%`} tone="success" />
          <HeroStat
            label="Pending review"
            value={stats.verdicts.awaiting_review.toLocaleString()}
            tone="warning"
          />
        </dl>
      </div>
    </Panel>
  );
}

function HeroStat({ label, value, tone = "primary" }: { label: string; value: string; tone?: Tone }) {
  return (
    <div className="px-4 sm:px-6">
      <dd className={`text-title2 font-extrabold tabular-nums ${toneText[tone]}`}>{value}</dd>
      <dt className="mt-0.5 text-caption font-medium text-text-muted">{label}</dt>
    </div>
  );
}

function KpiTiles({ stats }: { stats: DashboardStats }) {
  const { counts, baseline_readiness: readiness, verdicts } = stats;
  const tiles = [
    {
      label: "Fully locked baselines",
      value: `${readiness.ready} / ${counts.students}`,
      note: "Students with all 3 baseline samples",
      icon: UserCheckIcon,
      tone: "success" as Tone,
      href: "/students",
    },
    {
      label: "Submissions checked",
      value: counts.analyses.toLocaleString(),
      note: `Of ${counts.submissions.toLocaleString()} uploaded`,
      icon: TargetIcon,
      tone: "primary" as Tone,
      href: "/papers/analyze",
    },
    {
      label: "Matched baseline",
      value: verdicts.ai_consistent.toLocaleString(),
      note: `Scored at or above the ${verdicts.threshold}% threshold`,
      icon: ShieldIcon,
      tone: "success" as Tone,
      href: undefined,
    },
    {
      label: "Needs teacher audit",
      value: verdicts.ai_flagged.toLocaleString(),
      note: `Scored below the ${verdicts.threshold}% threshold`,
      icon: AlertTriangleIcon,
      tone: "warning" as Tone,
      href: undefined,
    },
  ];

  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
      {tiles.map((tile) => {
        const Icon = tile.icon;
        const body = (
          <>
            <div className="flex items-start justify-between gap-2">
              <p className="text-caption font-semibold uppercase tracking-wider text-text-muted">
                {tile.label}
              </p>
              <span
                className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-lg border ${toneIcon[tile.tone]}`}
              >
                <Icon className="h-4 w-4" />
              </span>
            </div>
            <p className={`mt-2 text-title1 font-extrabold tabular-nums ${toneText[tile.tone]}`}>
              {tile.value}
            </p>
            <p className="mt-1 text-caption text-text-subtle">{tile.note}</p>
          </>
        );
        const className =
          "block rounded-2xl border border-border bg-bg-elevated p-5 shadow-card transition-colors duration-200 ease-apple";
        return tile.href ? (
          <Link key={tile.label} href={tile.href} className={`${className} hover:border-border-strong`}>
            {body}
          </Link>
        ) : (
          <div key={tile.label} className={className}>
            {body}
          </div>
        );
      })}
    </div>
  );
}

/**
 * A submission from a student with no baseline is silently never analysed -
 * nothing else here would surface that.
 */
function BaselineWarnings({ stats }: { stats: DashboardStats }) {
  const { no_baseline } = stats.baseline_readiness;
  const unchecked = stats.counts.submissions - stats.counts.analyses;
  if (no_baseline <= 0 && unchecked <= 0) return null;

  return (
    <div className="space-y-2">
      {no_baseline > 0 ? (
        <Alert variant="warning">
          {no_baseline} {no_baseline === 1 ? "student has" : "students have"} no baseline yet.{" "}
          <Link href="/papers/baseline" className="font-medium underline">
            Add baseline papers
          </Link>
        </Alert>
      ) : null}
      {unchecked > 0 ? (
        <Alert variant="warning">
          {unchecked} {unchecked === 1 ? "submission was" : "submissions were"} saved without being
          analysed, because the student had no baseline at the time. Add one, then upload the
          submission again.
        </Alert>
      ) : null}
    </div>
  );
}

function SubmissionsQueue({ stats }: { stats: DashboardStats }) {
  const rows = stats.recent_activity;
  const threshold = stats.verdicts.threshold;

  return (
    <Panel>
      <PanelHeader
        title="Submissions Queue & Audit Log"
        subtitle="The latest baseline comparison scores across your classes."
        icon={<ClockIcon className="h-5 w-5 text-accent" />}
        action={
          <Link
            href="/papers/analyze"
            className="inline-flex items-center gap-1.5 rounded-lg bg-primary-600 px-3.5 py-2 text-footnote font-semibold text-white transition-colors duration-200 ease-apple hover:bg-primary-700"
          >
            <BoltIcon className="h-3.5 w-3.5" />
            Open Verification Studio
          </Link>
        }
      />

      {rows.length === 0 ? (
        <p className="px-5 pb-6 pt-4 text-subhead text-text-muted">
          Nothing checked yet.{" "}
          <Link href="/papers/analyze" className="font-medium text-primary-700 hover:underline">
            Check a submission
          </Link>
        </p>
      ) : (
        <div className="mt-4 overflow-x-auto px-5 pb-5">
          <table className="w-full min-w-[46rem] text-left">
            <thead>
              <tr className="bg-bg-subtle text-caption font-semibold uppercase tracking-wider text-text-muted">
                <th scope="col" className="rounded-l-lg px-4 py-3">Student</th>
                <th scope="col" className="px-4 py-3">Course</th>
                <th scope="col" className="px-4 py-3">Checked</th>
                <th scope="col" className="px-4 py-3">Consistency score</th>
                <th scope="col" className="px-4 py-3">System status</th>
                <th scope="col" className="rounded-r-lg px-4 py-3 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {rows.map((row) => (
                <QueueRow key={row.analysis_id} row={row} threshold={threshold} />
              ))}
            </tbody>
          </table>
        </div>
      )}
    </Panel>
  );
}

function QueueRow({ row, threshold }: { row: RecentAnalysis; threshold: number }) {
  const matches = row.consistency_score >= threshold;

  return (
    <tr className="text-footnote">
      <td className="px-4 py-3.5">
        <Link
          href={`/students/${row.student_id}`}
          className="font-semibold text-text hover:text-primary-700 hover:underline"
        >
          {row.student_name}
        </Link>
        <p className="font-mono text-[0.6875rem] text-text-subtle">
          WO-{String(row.student_id).padStart(4, "0")}
        </p>
      </td>
      <td className="px-4 py-3.5 text-text-muted">{row.subject_name}</td>
      <td className="px-4 py-3.5 text-text-muted">{formatDate(row.created_at)}</td>
      <td className="px-4 py-3.5">
        <span
          className={`inline-flex rounded-full border px-2.5 py-0.5 text-caption font-bold tabular-nums ${
            matches
              ? "border-success/40 bg-success-bg text-success"
              : "border-warning/40 bg-warning-bg text-warning"
          }`}
        >
          {formatPercentage(row.consistency_score)} match
        </span>
      </td>
      <td className="px-4 py-3.5">
        {/* The engine's verdict and the teacher's decision answer different
            questions, so both are shown rather than merged. */}
        <div className="flex flex-col items-start gap-1">
          {row.flagged ? (
            <span className="inline-flex items-center gap-1 rounded-md border border-warning/40 bg-warning-bg px-2 py-0.5 text-caption font-semibold text-warning">
              <AlertTriangleIcon className="h-3.5 w-3.5" />
              Review required
            </span>
          ) : (
            <span className="inline-flex items-center gap-1 text-caption font-semibold text-success">
              <CheckCircleIcon className="h-3.5 w-3.5" />
              Consistent with baseline
            </span>
          )}
          {row.teacher_decision ? (
            <span
              className={`text-caption font-medium ${
                row.teacher_decision === "flagged" ? "text-danger" : "text-primary-700"
              }`}
            >
              You: {row.teacher_decision}
            </span>
          ) : null}
        </div>
      </td>
      <td className="px-4 py-3.5 text-right">
        <Link
          href={`/analysis/${row.analysis_id}`}
          aria-label={`Inspect audit report for ${row.student_name}`}
          className="inline-flex items-center rounded-lg border border-border-strong bg-bg px-3 py-1.5 text-caption font-semibold text-text transition-colors duration-200 ease-apple hover:border-primary-400 hover:text-primary-700"
        >
          Inspect Audit Report
        </Link>
      </td>
    </tr>
  );
}

function BaselineReadiness({ stats }: { stats: DashboardStats }) {
  const { ready, needs_more_samples, no_baseline } = stats.baseline_readiness;
  const items = [
    { label: "Ready", value: ready, className: "text-success" },
    { label: "Need more samples", value: needs_more_samples, className: "text-warning" },
    { label: "No baseline", value: no_baseline, className: "text-danger" },
  ];

  return (
    <Panel>
      <PanelHeader
        title="Baseline readiness"
        subtitle="A student with no baseline on file can't be checked at all."
      />
      <div className="grid grid-cols-3 gap-3 p-5 text-center">
        {items.map((item) => (
          <div key={item.label} className="rounded-xl bg-bg-subtle p-3">
            <p className={`text-title2 font-extrabold tabular-nums ${item.className}`}>{item.value}</p>
            <p className="mt-0.5 text-caption text-text-muted">{item.label}</p>
          </div>
        ))}
      </div>
    </Panel>
  );
}

function ScoreHistogram({ stats }: { stats: DashboardStats }) {
  const buckets = stats.score_distribution;
  const max = Math.max(1, ...buckets.map((bucket) => bucket.count));
  const total = buckets.reduce((sum, bucket) => sum + bucket.count, 0);

  return (
    <Panel>
      <PanelHeader
        title="Score distribution"
        subtitle={
          total === 0
            ? "Appears once submissions have been checked."
            : `All ${total} analysed ${total === 1 ? "submission" : "submissions"}. Flag threshold: ${stats.verdicts.threshold}%.`
        }
      />
      {total > 0 ? (
        <div className="flex h-36 items-end gap-2 p-5">
          {buckets.map((bucket) => (
            <div key={bucket.label} className="flex h-full flex-1 flex-col items-center justify-end gap-1.5">
              <span className="text-caption tabular-nums text-text-muted">{bucket.count || ""}</span>
              <div
                className={`w-full rounded-t-md transition-[height] duration-500 ease-apple ${
                  bucket.upper < stats.verdicts.threshold ? "bg-warning/70" : "bg-primary-500"
                }`}
                style={{ height: `${Math.max(bucket.count > 0 ? 4 : 0, (bucket.count / max) * 100)}%` }}
              />
              <span className="text-caption text-text-subtle">{bucket.label}</span>
            </div>
          ))}
        </div>
      ) : null}
    </Panel>
  );
}

function Leaderboard({
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
    <Panel>
      <PanelHeader title={title} subtitle={subtitle} />
      <div className="p-5 pt-3">
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
                <span className="text-footnote text-text-muted">{row.submissions} checked</span>
                {row.flagged > 0 ? (
                  <span className="rounded-full border border-warning/40 bg-warning-bg px-2 py-0.5 text-caption font-semibold text-warning">
                    {row.flagged} flagged
                  </span>
                ) : row.average_score !== null ? (
                  <span className="text-footnote font-semibold tabular-nums text-success">
                    {formatPercentage(row.average_score)}
                  </span>
                ) : null}
              </li>
            ))}
          </ul>
        )}
      </div>
    </Panel>
  );
}

function DashboardSkeleton() {
  return (
    <SkeletonGroup className="space-y-6">
      <div className="rounded-2xl border border-border bg-bg-elevated p-8">
        <SkeletonBar className="h-5 w-64 rounded-full" />
        <SkeletonBar className="mt-4 h-8 w-80" />
        <SkeletonBar className="mt-3 h-4 w-full max-w-xl" />
      </div>
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {[0, 1, 2, 3].map((tile) => (
          <div key={tile} className="rounded-2xl border border-border bg-bg-elevated p-5">
            <SkeletonBar className="h-3 w-28" />
            <SkeletonBar className="mt-3 h-8 w-20" />
            <SkeletonBar className="mt-2 h-3 w-32" />
          </div>
        ))}
      </div>
      <div className="rounded-2xl border border-border bg-bg-elevated p-5">
        <SkeletonBar className="h-5 w-56" />
        <div className="mt-5 space-y-3">
          {[0, 1, 2].map((row) => (
            <SkeletonBar key={row} className="h-10 w-full" />
          ))}
        </div>
      </div>
    </SkeletonGroup>
  );
}
