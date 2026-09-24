"use client";

import { useRef, useState } from "react";

interface FileDropzoneProps {
  onFile: (file: File) => void;
  accept?: string;
  disabled?: boolean;
  hint?: string;
}

/**
 * Drag-and-drop file input.
 *
 * The visible drop area is a real `<button>` and the `<input type="file">`
 * is a sibling, so the control is reachable by keyboard and announced
 * properly - a `<div>` with an onDrop handler is neither.
 */
export default function FileDropzone({
  onFile,
  accept = ".pdf,.docx,.txt,.md",
  disabled = false,
  hint,
}: FileDropzoneProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [dragging, setDragging] = useState(false);

  function handleDrop(event: React.DragEvent) {
    event.preventDefault();
    setDragging(false);
    if (disabled) return;
    const file = event.dataTransfer.files?.[0];
    if (file) onFile(file);
  }

  return (
    <div>
      <button
        type="button"
        disabled={disabled}
        onClick={() => inputRef.current?.click()}
        onDragOver={(event) => {
          event.preventDefault();
          if (!disabled) setDragging(true);
        }}
        onDragLeave={() => setDragging(false)}
        onDrop={handleDrop}
        className={`flex w-full flex-col items-center justify-center rounded-xl border-2 border-dashed px-6 py-8 text-center transition-colors duration-200 ease-apple disabled:cursor-not-allowed disabled:opacity-60 ${
          dragging
            ? "border-primary-500 bg-primary-50"
            : "border-border hover:border-border-strong hover:bg-bg-subtle"
        }`}
      >
        <svg
          width="28"
          height="28"
          viewBox="0 0 24 24"
          fill="none"
          aria-hidden="true"
          className="mb-2 text-text-subtle"
        >
          <path
            d="M12 16V4m0 0L7.5 8.5M12 4l4.5 4.5M4 15v3a2 2 0 002 2h12a2 2 0 002-2v-3"
            stroke="currentColor"
            strokeWidth="1.6"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        </svg>
        <span className="text-subhead font-medium text-text">
          Drop a file here, or choose one
        </span>
        <span className="mt-1 text-footnote text-text-subtle">
          {hint ?? "PDF, Word or plain text"}
        </span>
      </button>
      <input
        ref={inputRef}
        type="file"
        accept={accept}
        className="sr-only"
        aria-label="Upload a document"
        disabled={disabled}
        onChange={(event) => {
          const file = event.target.files?.[0];
          if (file) onFile(file);
          // Reset so choosing the same file twice still fires a change.
          event.target.value = "";
        }}
      />
    </div>
  );
}
