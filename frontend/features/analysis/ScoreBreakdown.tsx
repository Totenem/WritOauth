"use client";

import type { BreakdownScore } from "@/types";
import { formatPercentage } from "@/utils/formatters";

const CATEGORY_LABELS: Record<keyof BreakdownScore, string> = {
  vocabulary: "Vocabulary",
  sentence_structure: "Sentence structure",
  grammar: "Grammar",
  readability: "Readability",
  style: "Style",
};

const CATEGORY_ORDER: (keyof BreakdownScore)[] = [
  "vocabulary",
  "sentence_structure",
  "grammar",
  "readability",
  "style",
];

/**
 * The five stylometric consistency scores, each 0-100, where higher means
 * "more like this student's baseline".
 *
 * The bars are a single neutral colour on purpose. There's no server-side
 * per-category threshold, so colouring them good/bad would be inventing a
 * judgement the backend never made.
 */
export default function ScoreBreakdown({ breakdown }: { breakdown: BreakdownScore }) {
  return (
    <div>
      <h2 className="text-lg font-medium text-text">Breakdown</h2>
      <p className="mt-1 text-sm text-text-muted">
        How closely each aspect of this submission matches the student&apos;s
        baseline. Higher is more consistent.
      </p>

      <dl className="mt-4 space-y-3">
        {CATEGORY_ORDER.map((category) => {
          const value = breakdown[category];
          return (
            <div key={category}>
              <div className="flex items-baseline justify-between">
                <dt className="text-sm text-text">{CATEGORY_LABELS[category]}</dt>
                <dd className="text-sm font-medium tabular-nums text-text">
                  {formatPercentage(value)}
                </dd>
              </div>
              <div
                role="meter"
                aria-label={CATEGORY_LABELS[category]}
                aria-valuenow={Math.round(value)}
                aria-valuemin={0}
                aria-valuemax={100}
                className="mt-1 h-2 w-full overflow-hidden rounded-full bg-bg-muted"
              >
                <div
                  className="h-full rounded-full bg-primary-600"
                  style={{ width: `${Math.max(0, Math.min(100, value))}%` }}
                />
              </div>
            </div>
          );
        })}
      </dl>
    </div>
  );
}
