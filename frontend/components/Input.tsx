import { forwardRef } from "react";

interface InputProps {
  label: string;
  name: string;
  type?: string;
  placeholder?: string;
  value?: string;
  onChange?: (e: React.ChangeEvent<HTMLInputElement>) => void;
  onBlur?: (e: React.FocusEvent<HTMLInputElement>) => void;
  error?: string;
  autoComplete?: string;
}

const Input = forwardRef<HTMLInputElement, InputProps>(function Input(
  { label, name, type = "text", placeholder, value, onChange, onBlur, error, autoComplete },
  ref
) {
  return (
    <div>
      <label htmlFor={name} className="mb-1 block text-sm font-medium text-text-muted">
        {label}
      </label>
      <input
        id={name}
        name={name}
        type={type}
        placeholder={placeholder}
        value={value}
        onChange={onChange}
        onBlur={onBlur}
        autoComplete={autoComplete}
        ref={ref}
        aria-invalid={error ? true : undefined}
        aria-describedby={error ? `${name}-error` : undefined}
        className={`block w-full rounded-lg border bg-bg-elevated px-3 py-2 text-subhead text-text placeholder:text-text-subtle focus:outline-none focus:ring-2 focus:ring-primary-500 ${
          error ? "border-danger" : "border-border-strong"
        }`}
      />
      {error && (
        <p id={`${name}-error`} className="mt-1 text-sm text-danger">
          {error}
        </p>
      )}
    </div>
  );
});

export default Input;
