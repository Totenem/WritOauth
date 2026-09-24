type AlertVariant = "info" | "success" | "warning" | "danger";

interface AlertProps {
  children: React.ReactNode;
  variant?: AlertVariant;
  title?: string;
  className?: string;
}

const variantClasses: Record<AlertVariant, string> = {
  info: "border-primary-200 bg-primary-50 text-primary-800",
  success: "border-success/25 bg-success-bg text-success",
  warning: "border-warning/25 bg-warning-bg text-warning",
  danger: "border-danger/25 bg-danger-bg text-danger",
};

/**
 * An inline banner. Replaces markup that was copy-pasted into roughly six
 * places, each with its own `role` handling.
 *
 * Errors are announced assertively; everything else politely.
 */
export default function Alert({
  children,
  variant = "info",
  title,
  className = "",
}: AlertProps) {
  return (
    <div
      role={variant === "danger" ? "alert" : "status"}
      data-variant={variant}
      className={`rounded-lg border px-4 py-3 text-subhead ${variantClasses[variant]} ${className}`}
    >
      {title ? <p className="font-semibold">{title}</p> : null}
      <div className={title ? "mt-0.5" : ""}>{children}</div>
    </div>
  );
}
