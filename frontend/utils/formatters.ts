/**
 * Formats a 0-1 ratio as a percentage (0.85 -> "85.0%").
 *
 * Careful: the analysis API mixes scales. `confidence_level` is a 0-1 ratio and
 * belongs here; `consistency_score` and the five `breakdown` values are already
 * on a 0-100 scale and must use `formatPercentage` instead, or a score of
 * 97.7468 would render as "9774.7%".
 */
export function formatScore(score: number): string {
  return `${(score * 100).toFixed(1)}%`;
}

/** Formats a value that is already on a 0-100 scale (97.7468 -> "97.7%"). */
export function formatPercentage(value: number): string {
  return `${value.toFixed(1)}%`;
}

export function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString("en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
}
