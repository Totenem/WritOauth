"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

/**
 * Baseline and Analyse are separate entries on purpose.
 *
 * There used to be a single "Papers" link pointing at /papers/baseline,
 * which left the analyse page unreachable from the navigation - a teacher
 * could upload baselines but had no way to check a submission.
 */
const NAV_GROUPS: {
  label: string | null;
  links: { href: string; label: string; description?: string }[];
}[] = [
  {
    label: null,
    links: [{ href: "/dashboard", label: "Dashboard" }],
  },
  {
    label: "Roster",
    links: [
      { href: "/students", label: "Students" },
      { href: "/subjects", label: "Subjects" },
    ],
  },
  {
    label: "Papers",
    links: [
      {
        href: "/papers/baseline",
        label: "Add baseline",
        description: "Teach the system a student's voice",
      },
      {
        href: "/papers/analyze",
        label: "Check a submission",
        description: "Compare new work to the baseline",
      },
    ],
  },
];

export default function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="hidden w-64 shrink-0 border-r border-border bg-bg-elevated md:block">
      <nav className="space-y-6 px-3 py-6">
        {NAV_GROUPS.map((group, index) => (
          <div key={group.label ?? `group-${index}`}>
            {group.label ? (
              <p className="px-3 pb-1.5 text-caption font-semibold uppercase tracking-wide text-text-subtle">
                {group.label}
              </p>
            ) : null}
            <ul className="space-y-0.5">
              {group.links.map((link) => {
                const isActive =
                  pathname === link.href ||
                  (pathname?.startsWith(`${link.href}/`) ?? false);
                return (
                  <li key={link.href}>
                    <Link
                      href={link.href}
                      aria-current={isActive ? "page" : undefined}
                      className={`block rounded-lg px-3 py-2 transition-colors duration-200 ease-apple ${
                        isActive
                          ? "bg-primary-50 text-primary-700"
                          : "text-text-muted hover:bg-bg-subtle hover:text-text"
                      }`}
                    >
                      <span className="block text-subhead font-medium">
                        {link.label}
                      </span>
                      {link.description ? (
                        <span
                          className={`mt-0.5 block text-caption ${
                            isActive ? "text-primary-600" : "text-text-subtle"
                          }`}
                        >
                          {link.description}
                        </span>
                      ) : null}
                    </Link>
                  </li>
                );
              })}
            </ul>
          </div>
        ))}
      </nav>
    </aside>
  );
}
