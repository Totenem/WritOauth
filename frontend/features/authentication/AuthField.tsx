"use client";

import { forwardRef, useState } from "react";
import { EyeIcon, EyeOffIcon } from "@/components/icons";

interface AuthFieldProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label: string;
  name: string;
  icon: React.ReactNode;
  error?: string;
}

const AuthField = forwardRef<HTMLInputElement, AuthFieldProps>(function AuthField(
  { label, name, icon, error, type = "text", ...rest },
  ref
) {
  const [revealed, setRevealed] = useState(false);
  const isPassword = type === "password";

  return (
    <div>
      <label htmlFor={name} className="mb-1.5 block text-footnote font-semibold text-brand-ink">
        {label}
      </label>
      <div className="relative">
        <span className="pointer-events-none absolute inset-y-0 left-3.5 flex items-center text-brand-navy/60">
          {icon}
        </span>
        <input
          id={name}
          name={name}
          ref={ref}
          type={isPassword && revealed ? "text" : type}
          aria-invalid={error ? true : undefined}
          aria-describedby={error ? `${name}-error` : undefined}
          className={`block h-12 w-full rounded-xl border bg-brand-cream/50 pl-10 text-subhead text-brand-ink transition-colors duration-200 ease-apple placeholder:text-brand-navy/40 focus:border-brand-gold focus:bg-white focus:outline-none focus:ring-2 focus:ring-brand-gold/30 ${
            isPassword ? "pr-11" : "pr-4"
          } ${error ? "border-red-500" : "border-brand-gold-pale"}`}
          {...rest}
        />
        {isPassword && (
          <button
            type="button"
            onClick={() => setRevealed((v) => !v)}
            aria-label={revealed ? "Hide password" : "Show password"}
            aria-pressed={revealed}
            className="absolute inset-y-0 right-1 flex w-10 items-center justify-center rounded-lg text-brand-navy/60 hover:text-brand-blue focus-visible:ring-brand-gold"
          >
            {revealed ? <EyeOffIcon /> : <EyeIcon />}
          </button>
        )}
      </div>
      {error && (
        <p id={`${name}-error`} className="mt-1.5 text-footnote text-red-600">
          {error}
        </p>
      )}
    </div>
  );
});

export default AuthField;
