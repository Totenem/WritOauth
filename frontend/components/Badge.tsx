interface BadgeProps {
  label: string;
  variant?: "success" | "warning" | "danger" | "info";
}

const variantClasses: Record<NonNullable<BadgeProps["variant"]>, string> = {
  success: "bg-success-bg text-success",
  warning: "bg-warning-bg text-warning",
  danger: "bg-danger-bg text-danger",
  info: "bg-primary-50 text-primary-700",
};

export default function Badge({ label, variant = "info" }: BadgeProps) {
  return (
    <span
      data-variant={variant}
      className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${variantClasses[variant]}`}
    >
      {label}
    </span>
  );
}
