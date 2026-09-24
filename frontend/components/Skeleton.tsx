interface SkeletonProps {
  /** Tailwind sizing/shape classes, e.g. "h-4 w-32". */
  className?: string;
}

/**
 * A content-shaped loading placeholder.
 *
 * Carries `role="status"` with the accessible name "Loading" so it is a
 * drop-in replacement for `Spinner` - existing tests assert on
 * `getByRole("status", { name: "Loading" })` and keep passing.
 *
 * Only the outermost skeleton in a group should be announced; nested ones
 * are decorative. Use `SkeletonGroup` to wrap several and announce once.
 */
export default function Skeleton({ className = "h-4 w-full" }: SkeletonProps) {
  return (
    <div
      role="status"
      aria-label="Loading"
      className={`relative overflow-hidden rounded-md bg-bg-muted ${className}`}
    >
      <div className="absolute inset-0 -translate-x-full animate-shimmer bg-gradient-to-r from-transparent via-bg-elevated/60 to-transparent" />
    </div>
  );
}

/** Groups decorative skeletons under a single announcement. */
export function SkeletonGroup({
  children,
  className = "",
}: {
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <div role="status" aria-label="Loading" className={className}>
      <div aria-hidden="true" className="contents">
        {children}
      </div>
    </div>
  );
}

/** A decorative bar, for use inside a SkeletonGroup. */
export function SkeletonBar({ className = "h-4 w-full" }: SkeletonProps) {
  return (
    <div
      aria-hidden="true"
      className={`relative overflow-hidden rounded-md bg-bg-muted ${className}`}
    >
      <div className="absolute inset-0 -translate-x-full animate-shimmer bg-gradient-to-r from-transparent via-bg-elevated/60 to-transparent" />
    </div>
  );
}
