import Link from "next/link";

interface PageHeaderProps {
  title: string;
  description?: React.ReactNode;
  /** A secondary route offered alongside this one. */
  alternate?: { href: string; label: string };
  actions?: React.ReactNode;
}

export default function PageHeader({
  title,
  description,
  alternate,
  actions,
}: PageHeaderProps) {
  return (
    <header className="mb-6 flex flex-wrap items-start justify-between gap-4">
      <div className="min-w-0">
        <h1 className="text-title1 font-semibold text-text">{title}</h1>
        {description ? (
          <p className="mt-1 max-w-2xl text-subhead text-text-muted">{description}</p>
        ) : null}
        {alternate ? (
          <Link
            href={alternate.href}
            className="mt-2 inline-block text-subhead text-primary-700 hover:underline"
          >
            {alternate.label} &rarr;
          </Link>
        ) : null}
      </div>
      {actions ? <div className="flex shrink-0 gap-2">{actions}</div> : null}
    </header>
  );
}
