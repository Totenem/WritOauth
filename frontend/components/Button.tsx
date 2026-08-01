interface ButtonProps {
  children: React.ReactNode;
  onClick?: () => void;
  disabled?: boolean;
  variant?: "primary" | "secondary" | "danger";
  type?: "button" | "submit" | "reset";
  className?: string;
}

const variantClasses: Record<NonNullable<ButtonProps["variant"]>, string> = {
  primary:
    "bg-primary-600 text-white hover:bg-primary-700 focus-visible:ring-primary-500 disabled:bg-primary-300",
  secondary:
    "bg-white text-primary-700 border border-border-strong hover:bg-bg-subtle focus-visible:ring-primary-500 disabled:text-text-subtle disabled:bg-bg-muted",
  danger:
    "bg-danger text-white hover:bg-red-700 focus-visible:ring-danger disabled:bg-red-300",
};

export default function Button({
  children,
  onClick,
  disabled = false,
  variant = "primary",
  type = "button",
  className = "",
}: ButtonProps) {
  return (
    <button
      type={type}
      onClick={onClick}
      disabled={disabled}
      data-variant={variant}
      className={`inline-flex items-center justify-center rounded-md px-4 py-2 text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 disabled:cursor-not-allowed ${variantClasses[variant]} ${className}`}
    >
      {children}
    </button>
  );
}
