interface ProgressProps {
  /** 0-100. Omit for an indeterminate bar. */
  value?: number;
  label: string;
  className?: string;
}

export default function Progress({ value, label, className = "" }: ProgressProps) {
  const indeterminate = value === undefined;
  const clamped = indeterminate ? 0 : Math.max(0, Math.min(100, value));

  return (
    <div
      role="progressbar"
      aria-label={label}
      aria-valuenow={indeterminate ? undefined : Math.round(clamped)}
      aria-valuemin={0}
      aria-valuemax={100}
      className={`h-1.5 w-full overflow-hidden rounded-full bg-bg-muted ${className}`}
    >
      <div
        className={`h-full rounded-full bg-primary-600 transition-[width] duration-300 ease-apple ${
          indeterminate ? "w-1/3 animate-shimmer" : ""
        }`}
        style={indeterminate ? undefined : { width: `${clamped}%` }}
      />
    </div>
  );
}
