interface CardProps {
  children: React.ReactNode;
  className?: string;
  /** Section heading rendered above the content. */
  title?: string;
  /** Supporting line under the title. */
  subtitle?: string;
  footer?: React.ReactNode;
  /** Set false for a card whose content manages its own padding. */
  padded?: boolean;
}

export default function Card({
  children,
  className = "",
  title,
  subtitle,
  footer,
  padded = true,
}: CardProps) {
  return (
    <div
      className={`rounded-xl border border-border bg-bg-elevated shadow-card ${className}`}
    >
      {title || subtitle ? (
        <div className={`${padded ? "px-5 pt-5" : "px-5 pt-5"}`}>
          {title ? (
            <h2 className="text-headline font-semibold text-text">{title}</h2>
          ) : null}
          {subtitle ? (
            <p className="mt-1 text-footnote text-text-muted">{subtitle}</p>
          ) : null}
        </div>
      ) : null}
      <div className={padded ? "p-5" : ""}>{children}</div>
      {footer ? (
        <div className="border-t border-border px-5 py-3">{footer}</div>
      ) : null}
    </div>
  );
}
