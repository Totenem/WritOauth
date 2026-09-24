import Link from "next/link";

interface EmptyStateProps {
  title: string;
  description?: string;
  /** A way forward. An empty state without one is a dead end. */
  actionLabel?: string;
  actionHref?: string;
  onAction?: () => void;
  icon?: React.ReactNode;
}

/**
 * The "nothing here yet" state.
 *
 * Always offers a next step where one exists: the previous version of this
 * app told teachers to "add a student before uploading a paper" without
 * linking to the page that does it.
 */
export default function EmptyState({
  title,
  description,
  actionLabel,
  actionHref,
  onAction,
  icon,
}: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center rounded-xl border border-dashed border-border bg-bg-subtle px-6 py-12 text-center">
      {icon ? (
        <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-bg-muted text-text-subtle">
          {icon}
        </div>
      ) : null}
      <p className="text-headline font-semibold text-text">{title}</p>
      {description ? (
        <p className="mt-1.5 max-w-sm text-subhead text-text-muted">{description}</p>
      ) : null}
      {actionLabel && actionHref ? (
        <Link
          href={actionHref}
          className="mt-5 inline-flex min-h-[44px] items-center justify-center rounded-lg bg-primary-600 px-4 text-subhead font-medium text-white transition-colors duration-200 ease-apple hover:bg-primary-700"
        >
          {actionLabel}
        </Link>
      ) : null}
      {actionLabel && !actionHref && onAction ? (
        <button
          type="button"
          onClick={onAction}
          className="mt-5 inline-flex min-h-[44px] items-center justify-center rounded-lg bg-primary-600 px-4 text-subhead font-medium text-white transition-colors duration-200 ease-apple hover:bg-primary-700"
        >
          {actionLabel}
        </button>
      ) : null}
    </div>
  );
}
