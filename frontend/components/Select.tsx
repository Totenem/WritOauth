import { forwardRef } from "react";

export interface SelectOption {
  value: number | string;
  label: string;
}

interface SelectProps {
  label: string;
  name: string;
  options: SelectOption[];
  /** Shown as a disabled first option so the field starts genuinely unselected. */
  placeholder?: string;
  value?: string;
  onChange?: (e: React.ChangeEvent<HTMLSelectElement>) => void;
  onBlur?: (e: React.FocusEvent<HTMLSelectElement>) => void;
  error?: string;
  disabled?: boolean;
  hint?: string;
}

const Select = forwardRef<HTMLSelectElement, SelectProps>(function Select(
  { label, name, options, placeholder, value, onChange, onBlur, error, disabled, hint },
  ref
) {
  const describedBy = error ? `${name}-error` : hint ? `${name}-hint` : undefined;

  return (
    <div>
      <label htmlFor={name} className="mb-1 block text-sm font-medium text-text-muted">
        {label}
      </label>
      <select
        id={name}
        name={name}
        value={value}
        onChange={onChange}
        onBlur={onBlur}
        ref={ref}
        disabled={disabled}
        aria-invalid={error ? true : undefined}
        aria-describedby={describedBy}
        className={`block w-full rounded-lg border bg-bg-elevated px-3 py-2 text-subhead text-text focus:outline-none focus:ring-2 focus:ring-primary-500 disabled:bg-bg-muted disabled:text-text-subtle ${
          error ? "border-danger" : "border-border-strong"
        }`}
      >
        {placeholder ? (
          <option value="">{placeholder}</option>
        ) : null}
        {options.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
      {error ? (
        <p id={`${name}-error`} className="mt-1 text-sm text-danger">
          {error}
        </p>
      ) : hint ? (
        <p id={`${name}-hint`} className="mt-1 text-subhead text-text-subtle">
          {hint}
        </p>
      ) : null}
    </div>
  );
});

export default Select;
