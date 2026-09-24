"use client";

import { useState } from "react";

import { Badge } from "@/components";
import type { AnalysisBreakdown, FeatureBreakdown, ProfileKey } from "@/types";
import { PROFILE_ORDER } from "@/types";
import { formatPercentage } from "@/utils/formatters";

const PROFILE_DESCRIPTIONS: Record<ProfileKey, string> = {
  stylistic:
    "Function words, transitions, pronouns and habitual phrasing. The strongest authorship signal, because these choices are largely unconscious and don't change with the topic.",
  syntactic:
    "Sentence length and variation, clause complexity and how sentences open.",
  lexical: "Vocabulary range, word length and how densely packed the writing is.",
  mechanical:
    "Spelling, punctuation, capitalisation and apostrophe habits.",
  discourse:
    "Paragraph shape, how ideas connect between sentences, and reading difficulty.",
  grammatical:
    "Grammatical error patterns. Low recall by design: it catches a minority of errors and is not a measure of the student's grammatical ability.",
};

/**
 * The six authorship profiles, each expandable to the features behind it.
 *
 * Bars are a single neutral colour on purpose. The backend asserts one
 * verdict - `flagged`, against its own threshold - and it applies to the
 * overall score, not to individual profiles. Colouring each bar good/bad
 * would invent six judgements the engine never made.
 */
export default function ScoreBreakdown({
  breakdown,
}: {
  breakdown: AnalysisBreakdown;
}) {
  return (
    <div>
      <h2 className="text-headline font-semibold text-text">
        Six authorship profiles
      </h2>
      <p className="mt-1 text-footnote text-text-muted">
        How closely each aspect of this submission matches the student&apos;s own
        baseline. Higher is more consistent. Expand a profile to see what drove
        its score.
      </p>

      <div className="mt-4 divide-y divide-border border-y border-border">
        {PROFILE_ORDER.map((key) => {
          const profile = breakdown.profiles[key];
          if (!profile) return null;
          return <ProfileRow key={key} profileKey={key} profile={profile} />;
        })}
      </div>
    </div>
  );
}

function ProfileRow({
  profileKey,
  profile,
}: {
  profileKey: ProfileKey;
  profile: AnalysisBreakdown["profiles"][ProfileKey];
}) {
  const [expanded, setExpanded] = useState(false);
  const scored = profile.available && profile.score !== null;

  return (
    <div className="py-3">
      <button
        type="button"
        onClick={() => setExpanded((open) => !open)}
        aria-expanded={expanded}
        className="flex w-full items-center gap-3 text-left"
      >
        <span className="flex-1">
          <span className="flex items-baseline justify-between gap-3">
            <span className="text-subhead font-medium text-text">
              {profile.label}
            </span>
            {scored ? (
              <span className="text-subhead font-semibold tabular-nums text-text">
                {formatPercentage(profile.score as number)}
              </span>
            ) : (
              <span className="text-footnote text-text-subtle">Not measured</span>
            )}
          </span>
          {scored ? (
            <span
              role="meter"
              aria-label={profile.label}
              aria-valuenow={Math.round(profile.score as number)}
              aria-valuemin={0}
              aria-valuemax={100}
              className="mt-1.5 block h-2 w-full overflow-hidden rounded-full bg-bg-muted"
            >
              <span
                className="block h-full rounded-full bg-primary-600 transition-[width] duration-500 ease-apple"
                style={{
                  width: `${Math.max(0, Math.min(100, profile.score as number))}%`,
                }}
              />
            </span>
          ) : (
            <span className="mt-1 block text-footnote text-text-subtle">
              {profile.suppressed_reason}
            </span>
          )}
        </span>
        <Chevron open={expanded} />
      </button>

      {expanded ? (
        <div className="mt-3 rounded-lg bg-bg-subtle p-3">
          <p className="text-footnote text-text-muted">
            {PROFILE_DESCRIPTIONS[profileKey]}
          </p>
          <ul className="mt-3 space-y-2">
            {profile.features.map((feature) => (
              <FeatureRow key={feature.key} feature={feature} />
            ))}
          </ul>
        </div>
      ) : null}
    </div>
  );
}

function FeatureRow({ feature }: { feature: FeatureBreakdown }) {
  if (!feature.available) {
    return (
      <li className="flex items-baseline justify-between gap-3 text-footnote">
        <span className="text-text-subtle">{feature.label}</span>
        <span className="shrink-0 text-text-subtle">
          {feature.suppressed_reason}
        </span>
      </li>
    );
  }

  return (
    <li className="flex items-baseline justify-between gap-3 text-footnote">
      <span className="flex flex-wrap items-center gap-1.5 text-text-muted">
        {feature.label}
        {feature.measurement === "approximation" ? (
          <span title={feature.note || "An approximate measure with known limits."}>
            <Badge label="approx" variant="warning" />
          </span>
        ) : null}
      </span>
      <span className="shrink-0 tabular-nums text-text">
        {describeDeviation(feature)}
      </span>
    </li>
  );
}

/**
 * Says which way a feature moved, not just how far.
 *
 * Distributions are compared by a divergence that is always positive, so
 * "higher" would be meaningless for them.
 */
function describeDeviation(feature: FeatureBreakdown): string {
  if (Math.abs(feature.z) < 1) return "typical";
  if (feature.kind === "distribution") return "differs";
  return feature.z > 0 ? "higher" : "lower";
}

function Chevron({ open }: { open: boolean }) {
  return (
    <svg
      width="14"
      height="14"
      viewBox="0 0 16 16"
      fill="none"
      aria-hidden="true"
      className={`shrink-0 text-text-subtle transition-transform duration-200 ease-apple ${
        open ? "rotate-90" : ""
      }`}
    >
      <path
        d="M6 3.5L10.5 8 6 12.5"
        stroke="currentColor"
        strokeWidth="1.6"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}
