"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useRef, useState } from "react";
import { useQuery } from "@tanstack/react-query";

import api from "@/services/api";
import type { Teacher } from "@/types";
import ThemeToggle from "./ThemeToggle";
import {
  BoltIcon,
  BookIcon,
  ChartIcon,
  ChevronDownIcon,
  LogOutIcon,
  UploadIcon,
  UsersIcon,
} from "./icons";

const TABS = [
  { href: "/dashboard", label: "Overview & Auditing", icon: ChartIcon, also: ["/analysis"] },
  { href: "/students", label: "Student Baseline Roster", icon: UsersIcon },
  { href: "/papers/baseline", label: "Baseline Setup", icon: UploadIcon },
  { href: "/papers/analyze", label: "Verification Studio", icon: BoltIcon, also: ["/papers/"] },
  { href: "/subjects", label: "Courses", icon: BookIcon },
];

function isTabActive(pathname: string, tab: (typeof TABS)[number]) {
  if (pathname === tab.href || pathname.startsWith(`${tab.href}/`)) return true;
  // Paper detail pages (/papers/:id) belong to the studio, but the baseline
  // upload page has its own tab.
  return (tab.also ?? []).some(
    (prefix) => pathname.startsWith(prefix) && !pathname.startsWith("/papers/baseline")
  );
}

function initials(name: string) {
  return name
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0]!.toUpperCase())
    .join("");
}

interface AppHeaderProps {
  teacher?: Teacher;
  onLogout: () => void;
}

export default function AppHeader({ teacher, onLogout }: AppHeaderProps) {
  const pathname = usePathname() ?? "";

  return (
    <header className="sticky top-0 z-30 border-b border-border bg-bg-elevated/85 backdrop-blur-xl">
      <div className="mx-auto flex h-16 max-w-6xl items-center justify-between gap-4 px-4 sm:px-6">
        <Link href="/dashboard" className="flex items-center gap-3 rounded-lg">
          <span className="flex h-10 w-10 items-center justify-center rounded-xl border-2 border-brand-gold bg-brand-ink text-footnote font-extrabold tracking-tight text-brand-cream">
            WO
          </span>
          <span className="leading-tight">
            <span className="block text-headline font-extrabold tracking-tight text-text">
              Writ <span className="text-accent">Oath</span>
            </span>
            <span className="hidden text-[0.625rem] font-bold uppercase tracking-[0.14em] text-primary-700 sm:block">
              Educator Portal
            </span>
          </span>
        </Link>

        <div className="flex items-center gap-3">
          <ThemeToggle />
          <UserMenu teacher={teacher} onLogout={onLogout} />
        </div>
      </div>

      <div className="mx-auto flex max-w-6xl items-center gap-4 px-4 pb-2.5 sm:px-6">
        <nav aria-label="Primary" className="-mx-1 flex flex-1 gap-1 overflow-x-auto px-1">
          {TABS.map((tab) => {
            const active = isTabActive(pathname, tab);
            const Icon = tab.icon;
            return (
              <Link
                key={tab.href}
                href={tab.href}
                aria-current={active ? "page" : undefined}
                className={`flex shrink-0 items-center gap-1.5 whitespace-nowrap rounded-lg border px-3 py-1.5 text-footnote font-medium transition-colors duration-200 ease-apple ${
                  active
                    ? "border-primary-300 bg-primary-50 text-primary-700"
                    : "border-transparent text-text-muted hover:bg-bg-subtle hover:text-text"
                }`}
              >
                <Icon className="h-3.5 w-3.5" />
                {tab.label}
              </Link>
            );
          })}
        </nav>
        <EngineStatus />
      </div>
    </header>
  );
}

function EngineStatus() {
  const { isPending, isError } = useQuery({
    queryKey: ["health"],
    queryFn: () => api.get("/health").then((res) => res.data),
    refetchInterval: 60_000,
    retry: false,
  });

  const [dot, label] = isPending
    ? ["bg-text-subtle", "Checking engine…"]
    : isError
      ? ["bg-danger", "Engine unreachable"]
      : ["bg-success", "Analysis engine online"];

  return (
    <p className="hidden shrink-0 items-center gap-1.5 text-caption font-medium text-text-muted lg:flex">
      <span className={`h-2 w-2 rounded-full ${dot}`} aria-hidden="true" />
      {label}
    </p>
  );
}

function UserMenu({ teacher, onLogout }: AppHeaderProps) {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;
    const onPointer = (e: MouseEvent) => {
      if (!ref.current?.contains(e.target as Node)) setOpen(false);
    };
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && setOpen(false);
    document.addEventListener("mousedown", onPointer);
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("mousedown", onPointer);
      document.removeEventListener("keydown", onKey);
    };
  }, [open]);

  const name = teacher?.name ?? "Educator";

  return (
    <div ref={ref} className="relative">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        aria-expanded={open}
        aria-haspopup="menu"
        className="flex items-center gap-2.5 rounded-xl p-1 text-left hover:bg-bg-subtle"
      >
        <span className="hidden text-right leading-tight sm:block">
          <span className="block text-footnote font-semibold text-text">{name}</span>
          {teacher?.email ? (
            <span className="block text-caption text-text-subtle">{teacher.email}</span>
          ) : null}
        </span>
        <span className="flex h-9 w-9 items-center justify-center rounded-full bg-primary-600 text-caption font-bold text-white ring-2 ring-primary-200">
          {initials(name)}
        </span>
        <ChevronDownIcon className="hidden h-3.5 w-3.5 text-text-subtle sm:block" />
      </button>

      {open ? (
        <div
          role="menu"
          className="absolute right-0 mt-2 w-56 animate-scale-in rounded-xl border border-border bg-bg-elevated p-1.5 shadow-overlay"
        >
          <div className="px-3 py-2 sm:hidden">
            <p className="text-footnote font-semibold text-text">{name}</p>
            {teacher?.email ? <p className="text-caption text-text-subtle">{teacher.email}</p> : null}
          </div>
          <button
            type="button"
            role="menuitem"
            onClick={onLogout}
            className="flex w-full items-center gap-2 rounded-lg px-3 py-2 text-footnote font-medium text-danger hover:bg-danger-bg"
          >
            <LogOutIcon className="h-4 w-4" />
            Log out
          </button>
        </div>
      ) : null}
    </div>
  );
}
