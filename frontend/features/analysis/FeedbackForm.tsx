"use client";

import { useForm } from "react-hook-form";
import { Button, Textarea } from "@/components";
import { useSubmitFeedback } from "@/hooks/useAnalysis";
import type { Feedback, FeedbackDecision } from "@/types";
import { getApiErrorMessage } from "@/utils/apiError";
import { formatDate } from "@/utils/formatters";

interface FeedbackFormValues {
  decision: FeedbackDecision | "";
  remarks: string;
}

const DECISIONS: { value: FeedbackDecision; label: string; description: string }[] = [
  {
    value: "genuine",
    label: "Genuine",
    description: "I'm satisfied this is the student's own work.",
  },
  {
    value: "flagged",
    label: "Flagged",
    description: "This needs following up with the student.",
  },
];

export default function FeedbackForm({ analysisId }: { analysisId: number }) {
  const submitFeedback = useSubmitFeedback(analysisId);
  const saved: Feedback | undefined = submitFeedback.data;

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<FeedbackFormValues>({ defaultValues: { decision: "", remarks: "" } });

  const onSubmit = async (values: FeedbackFormValues) => {
    try {
      await submitFeedback.mutateAsync({
        decision: values.decision as FeedbackDecision,
        // The API takes `remarks: str | null`; send null rather than "" so an
        // untouched box doesn't read as a deliberate empty remark.
        remarks: values.remarks.trim() || null,
      });
    } catch {
      // The error is rendered below.
    }
  };

  return (
    <div>
      <h2 className="text-lg font-medium text-text">Your decision</h2>
      <p className="mt-1 text-sm text-text-muted">
        The score is a signal, not a verdict — record what you concluded.
      </p>

      {saved ? (
        <div
          role="status"
          className="mt-4 rounded-md border border-border bg-bg-subtle p-3 text-sm"
        >
          <p className="text-text">
            Recorded as{" "}
            <strong className="font-semibold">
              {saved.decision === "flagged" ? "Flagged" : "Genuine"}
            </strong>{" "}
            on {formatDate(saved.created_at)}.
          </p>
          {saved.remarks ? (
            <p className="mt-1 text-text-muted">&ldquo;{saved.remarks}&rdquo;</p>
          ) : null}
          <p className="mt-2 text-text-subtle">
            Submitting again replaces this decision.
          </p>
        </div>
      ) : null}

      <form onSubmit={handleSubmit(onSubmit)} noValidate className="mt-4 space-y-4">
        <fieldset>
          <legend className="mb-2 text-sm font-medium text-text-muted">Decision</legend>
          <div className="space-y-2">
            {DECISIONS.map((option) => (
              <label
                key={option.value}
                htmlFor={`decision-${option.value}`}
                className="flex cursor-pointer gap-3 rounded-md border border-border p-3 hover:bg-bg-subtle"
              >
                <input
                  id={`decision-${option.value}`}
                  type="radio"
                  value={option.value}
                  className="mt-1"
                  {...register("decision", { required: "Choose a decision" })}
                />
                <span>
                  <span className="block text-sm font-medium text-text">
                    {option.label}
                  </span>
                  <span className="block text-sm text-text-muted">
                    {option.description}
                  </span>
                </span>
              </label>
            ))}
          </div>
          {errors.decision?.message ? (
            <p className="mt-1 text-sm text-danger">{errors.decision.message}</p>
          ) : null}
        </fieldset>

        <Textarea
          label="Remarks (optional)"
          rows={4}
          placeholder="Anything worth recording for later..."
          {...register("remarks")}
        />

        {submitFeedback.isError ? (
          <p role="alert" className="text-sm text-danger">
            {getApiErrorMessage(submitFeedback.error)}
          </p>
        ) : null}

        <Button type="submit" disabled={submitFeedback.isPending}>
          {submitFeedback.isPending
            ? "Saving..."
            : saved
              ? "Update decision"
              : "Save decision"}
        </Button>
      </form>
    </div>
  );
}
