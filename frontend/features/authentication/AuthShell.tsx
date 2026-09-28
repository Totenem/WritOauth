"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";
import {
  ArrowRightIcon,
  BookIcon,
  ChartIcon,
  CheckCircleIcon,
  ChipIcon,
  DocSearchIcon,
  LayersIcon,
  ShieldIcon,
  SparkleIcon,
} from "@/components/icons";

const NAV_LINKS = [
  { label: "Home", href: "/" },
  { label: "How It Works", href: "/#how-it-works" },
  { label: "Sample Report", href: "/#sample-report" },
  { label: "Pricing", href: "/#pricing" },
  { label: "Contact", href: "/#contact" },
];

const STEPS = [
  {
    icon: BookIcon,
    title: "Establish 3 Verified Baseline Samples",
    tag: "Knowledge Base Foundation",
    body: "Each student submits 3 verified historical writing samples across diverse topics to construct their unique stylistic baseline profile.",
  },
  {
    icon: ChipIcon,
    title: "Stylometric Feature Extraction",
    tag: "Quantitative Analysis",
    body: "WritOath extracts over 40 quantitative markers including sentence complexity, lexical diversity, punctuation habits, and syntactic depth.",
  },
  {
    icon: DocSearchIcon,
    title: "RAG & Semantic Vector Retrieval",
    tag: "Contextual Match",
    body: "When a new paper is uploaded, Retrieval-Augmented Generation searches the student's verified writing history for contextually relevant passages.",
  },
  {
    icon: CheckCircleIcon,
    title: "Explainable Score & Teacher Validation",
    tag: "Human-in-the-Loop",
    body: "An open-source LLM produces a detailed consistency score with evidence snippets. Teachers review and validate findings to continuously train the profile.",
  },
];

const SAMPLE_PROFILES = [
  { label: "Stylistic", score: 91 },
  { label: "Syntactic", score: 88 },
  { label: "Lexical", score: 84 },
  { label: "Mechanical", score: 79 },
  { label: "Discourse", score: 86 },
  { label: "Grammatical", score: 90 },
];

type Tab = "how" | "sample";

export default function AuthShell({ children }: { children: React.ReactNode }) {
  const [tab, setTab] = useState<Tab>("how");
  const pathname = usePathname();
  const active = pathname.startsWith("/register") ? "register" : "login";

  return (
    <div className="min-h-screen bg-brand-cream text-brand-ink">
      <div className="bg-brand-ink px-4 py-2 text-center text-caption text-brand-cream sm:text-footnote">
        <SparkleIcon className="mr-1.5 inline h-3.5 w-3.5 text-brand-gold-light" />
        <span className="font-medium">
          &ldquo;Don&apos;t detect artificial intelligence. Verify authentic authorship.&rdquo;
        </span>
        <span className="mx-2 hidden text-brand-gold-light sm:inline">
          &bull; <span className="font-semibold">Version 1.0 Philosophy</span>
        </span>
        <Link
          href="/#how-it-works"
          className="ml-1 inline-flex items-center gap-0.5 font-medium text-brand-gold-pale underline underline-offset-2 hover:text-white"
        >
          Read Framework <ArrowRightIcon className="h-3 w-3" />
        </Link>
      </div>

      <header className="mx-auto flex max-w-6xl items-center justify-between gap-4 border-b border-brand-gold-pale/60 px-4 py-4 sm:px-6">
        <Link href="/" className="flex items-center gap-2.5">
          <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-brand-ink text-brand-gold-light">
            <ShieldIcon className="h-5 w-5" />
          </span>
          <span className="text-title3 font-extrabold tracking-tight text-brand-ink">
            Writ<span className="text-brand-blue-light">Oath</span>
          </span>
          <span className="hidden rounded-md bg-brand-blue/10 px-1.5 py-0.5 text-[0.625rem] font-bold uppercase tracking-wider text-brand-blue sm:inline">
            Educators
          </span>
        </Link>

        <nav aria-label="Main" className="hidden items-center gap-7 lg:flex">
          {NAV_LINKS.map((link) => (
            <Link
              key={link.label}
              href={link.href}
              className="text-footnote font-medium text-brand-navy/80 transition-colors hover:text-brand-blue"
            >
              {link.label}
            </Link>
          ))}
        </nav>

        <div className="flex items-center gap-2">
          <Link
            href="/register"
            scroll={false}
            aria-current={active === "register" ? "page" : undefined}
            className="rounded-lg px-3 py-2 text-footnote font-semibold text-brand-ink hover:text-brand-blue"
          >
            Sign Up
          </Link>
          <Link
            href="/login"
            scroll={false}
            aria-current={active === "login" ? "page" : undefined}
            className="rounded-lg bg-gradient-to-r from-brand-gold to-brand-gold-light px-5 py-2 text-footnote font-semibold text-brand-ink shadow-sm transition-opacity hover:opacity-90"
          >
            Login
          </Link>
        </div>
      </header>

      <main className="mx-auto grid max-w-6xl gap-10 px-4 py-10 sm:px-6 lg:grid-cols-[1fr_minmax(0,26rem)] lg:gap-16 lg:py-12">
        <section className="order-2 lg:order-1" aria-labelledby="auth-hero-title">
          <div className="flex flex-wrap items-center gap-3">
            <span className="rounded-md bg-brand-gold-pale/50 px-3 py-1 text-caption font-bold uppercase tracking-[0.12em] text-brand-blue">
              Authorship Verification Platform
            </span>
            <div role="tablist" aria-label="Preview" className="flex rounded-xl border border-brand-gold-pale bg-white p-1">
              <TabButton selected={tab === "how"} onClick={() => setTab("how")} icon={<LayersIcon className="h-3.5 w-3.5" />}>
                How It Works
              </TabButton>
              <TabButton selected={tab === "sample"} onClick={() => setTab("sample")} icon={<ChartIcon className="h-3.5 w-3.5" />}>
                Sample Report
              </TabButton>
            </div>
          </div>

          <h1 id="auth-hero-title" className="mt-6 text-[2rem] font-extrabold leading-tight tracking-tight text-brand-ink sm:text-[2.5rem]">
            Personalized Authorship Verification
          </h1>
          <p className="mt-3 max-w-xl text-subhead text-brand-navy/70">
            Instead of judging essays in isolation, WritOath continuously compares newly submitted
            assignments against each student&apos;s verified baseline writing profile.
          </p>

          <div role="tabpanel" className="mt-6">
            {tab === "how" ? <StepList /> : <SampleReport />}
          </div>

          <div className="mt-4 flex flex-wrap items-center justify-between gap-2 rounded-xl border border-brand-gold-pale bg-white/70 px-4 py-3">
            <p className="flex items-center gap-2 text-footnote font-medium text-brand-navy">
              <ShieldIcon className="h-4 w-4 text-brand-gold" />
              Designed for 5&ndash;10 Teachers &amp; 100&ndash;200 Students per Pilot
            </p>
            {tab === "how" && (
              <button
                type="button"
                onClick={() => setTab("sample")}
                className="inline-flex items-center gap-1 text-footnote font-semibold text-brand-blue hover:text-brand-blue-light"
              >
                See Sample Report <ArrowRightIcon className="h-3.5 w-3.5" />
              </button>
            )}
          </div>
        </section>

        <div className="order-1 lg:order-2">
          {/* Keyed so the card replays its entrance when switching forms. */}
          <div key={active} className="animate-scale-in">
            {children}
          </div>
        </div>
      </main>
    </div>
  );
}

function TabButton({
  selected,
  onClick,
  icon,
  children,
}: {
  selected: boolean;
  onClick: () => void;
  icon: React.ReactNode;
  children: React.ReactNode;
}) {
  return (
    <button
      type="button"
      role="tab"
      aria-selected={selected}
      onClick={onClick}
      className={`flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-caption font-semibold transition-colors duration-200 ease-apple ${
        selected ? "bg-brand-ink text-white" : "text-brand-blue hover:bg-brand-cream"
      }`}
    >
      {icon}
      {children}
    </button>
  );
}

function StepList() {
  const [activeStep, setActiveStep] = useState(0);

  return (
    <ol className="space-y-3">
      {STEPS.map((step, i) => {
        const Icon = step.icon;
        const isActive = i === activeStep;
        return (
          <li key={step.title}>
            <button
              type="button"
              onClick={() => setActiveStep(i)}
              aria-current={isActive ? "step" : undefined}
              className={`flex w-full gap-4 rounded-2xl border bg-white/80 p-4 text-left transition-all duration-200 ease-apple hover:border-brand-gold-light ${
                isActive ? "border-brand-gold shadow-[0_4px_16px_rgb(184_147_67/0.15)]" : "border-brand-gold-pale/70"
              }`}
            >
              <span
                className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-xl ${
                  isActive ? "bg-brand-ink text-brand-gold-light" : "bg-brand-cream text-brand-navy"
                }`}
              >
                <Icon />
              </span>
              <span className="min-w-0 flex-1">
                <span className="flex flex-wrap items-center justify-between gap-2">
                  <span className="text-footnote font-bold text-brand-ink">
                    <span className="mr-2 font-semibold text-brand-gold">Step 0{i + 1}</span>
                    {step.title}
                  </span>
                  <span className="rounded-md bg-brand-blue/10 px-2 py-0.5 text-[0.6875rem] font-medium text-brand-blue">
                    {step.tag}
                  </span>
                </span>
                <span className="mt-1 block text-caption text-brand-navy/70">{step.body}</span>
              </span>
            </button>
          </li>
        );
      })}
    </ol>
  );
}

function SampleReport() {
  return (
    <div className="rounded-2xl border border-brand-gold-pale bg-white/80 p-5">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <p className="text-caption font-semibold uppercase tracking-wider text-brand-gold">
            Illustrative sample
          </p>
          <p className="mt-1 text-headline font-bold text-brand-ink">Argumentative Essay &mdash; Student #042</p>
          <p className="text-caption text-brand-navy/60">Compared against 3 verified baseline papers</p>
        </div>
        <div className="text-right">
          <p className="text-[2rem] font-extrabold leading-none text-brand-blue">87%</p>
          <p className="mt-1 text-caption font-medium text-brand-navy/70">Consistency score</p>
        </div>
      </div>

      <ul className="mt-5 grid gap-3 sm:grid-cols-2">
        {SAMPLE_PROFILES.map((p) => (
          <li key={p.label}>
            <div className="flex justify-between text-caption">
              <span className="font-semibold text-brand-ink">{p.label}</span>
              <span className="tabular-nums text-brand-navy/70">{p.score}%</span>
            </div>
            <div className="mt-1 h-1.5 overflow-hidden rounded-full bg-brand-cream">
              <div
                className="h-full rounded-full bg-gradient-to-r from-brand-blue to-brand-blue-light"
                style={{ width: `${p.score}%` }}
              />
            </div>
          </li>
        ))}
      </ul>

      <p className="mt-5 rounded-xl bg-brand-cream/70 p-3 text-caption text-brand-navy/80">
        Sentence rhythm, vocabulary range, and punctuation habits closely match this student&apos;s
        baseline. Final judgement stays with the teacher.
      </p>
    </div>
  );
}
