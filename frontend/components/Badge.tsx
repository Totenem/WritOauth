interface BadgeProps {
  label: string;
  variant?: "success" | "warning" | "danger" | "info";
}

export default function Badge({ label, variant = "info" }: BadgeProps) {
  return <span data-variant={variant}>{label}</span>;
}
