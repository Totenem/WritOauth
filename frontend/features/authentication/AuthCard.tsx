import { GoogleIcon } from "@/components/icons";

export function AuthCard({
  title,
  subtitle,
  children,
}: {
  title: string;
  subtitle: string;
  children: React.ReactNode;
}) {
  return (
    <div className="rounded-[1.75rem] border border-brand-gold-pale/70 bg-white p-6 shadow-[0_8px_40px_rgb(5_16_45/0.08)] sm:p-8">
      <div className="mb-6 text-center">
        <h2 className="text-[1.75rem] font-extrabold tracking-tight text-brand-ink">{title}</h2>
        <p className="mt-1 text-footnote text-brand-blue">{subtitle}</p>
      </div>
      {children}
    </div>
  );
}

export function SubmitButton({ busy, children }: { busy: boolean; children: React.ReactNode }) {
  return (
    <button
      type="submit"
      disabled={busy}
      className="flex h-12 w-full items-center justify-center rounded-xl bg-gradient-to-r from-brand-gold via-brand-gold-light to-brand-gold-pale text-subhead font-semibold text-brand-ink shadow-[0_6px_16px_rgb(184_147_67/0.3)] transition-all duration-200 ease-apple hover:shadow-[0_8px_20px_rgb(184_147_67/0.4)] hover:brightness-105 focus-visible:ring-brand-gold disabled:cursor-not-allowed disabled:opacity-60"
    >
      {children}
    </button>
  );
}

export function FormError({ message }: { message: string }) {
  return (
    <p role="alert" className="rounded-xl bg-red-50 px-3 py-2 text-footnote text-red-700">
      {message}
    </p>
  );
}

export function OrDivider() {
  return (
    <div className="flex items-center gap-3 text-caption font-medium uppercase text-brand-navy/50">
      <span className="h-px flex-1 bg-brand-gold-pale" />
      or
      <span className="h-px flex-1 bg-brand-gold-pale" />
    </div>
  );
}

// Backend has no OAuth endpoint yet; shown for layout parity with the design.
export function GoogleButton() {
  return (
    <button
      type="button"
      disabled
      title="Google sign-in is coming soon"
      className="flex h-12 w-full cursor-not-allowed items-center justify-center gap-2.5 rounded-xl border border-brand-gold-pale bg-brand-cream/40 text-subhead font-semibold text-brand-ink/60"
    >
      <GoogleIcon />
      Continue with Google
      <span className="rounded-md bg-brand-gold-pale/60 px-1.5 py-0.5 text-[0.625rem] font-bold uppercase text-brand-navy">
        Soon
      </span>
    </button>
  );
}
