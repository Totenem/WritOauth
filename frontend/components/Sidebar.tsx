"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const NAV_LINKS = [
  { href: "/dashboard", label: "Dashboard" },
  { href: "/students", label: "Students" },
  { href: "/subjects", label: "Subjects" },
  { href: "/papers/baseline", label: "Papers" },
];

export default function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="w-64 shrink-0 border-r border-border bg-white">
      <p className="px-4 pb-2 pt-6 text-xs font-semibold uppercase tracking-wide text-text-subtle">
        Navigation
      </p>
      <nav>
        <ul className="space-y-1 px-2">
          {NAV_LINKS.map((link) => {
            const isActive =
              pathname === link.href || (pathname?.startsWith(`${link.href}/`) ?? false);
            return (
              <li key={link.href}>
                <Link
                  href={link.href}
                  className={`block rounded-md px-3 py-2 text-sm font-medium transition-colors ${
                    isActive
                      ? "bg-primary-50 text-primary-700"
                      : "text-text-muted hover:bg-bg-subtle hover:text-text"
                  }`}
                >
                  {link.label}
                </Link>
              </li>
            );
          })}
        </ul>
      </nav>
    </aside>
  );
}
