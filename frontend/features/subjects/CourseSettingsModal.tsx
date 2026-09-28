"use client";

import { useState } from "react";

import { Alert, Button, Modal, useToast } from "@/components";
import { useDeleteSubject, useUpdateSubject } from "@/hooks/useSubjects";
import type { Subject } from "@/types";
import { getApiErrorMessage } from "@/utils/apiError";
import SubjectForm from "./SubjectForm";

interface CourseSettingsModalProps {
  subject: Subject | null;
  onClose: () => void;
  /** Called after a successful delete, e.g. to leave a page that no longer exists. */
  onDeleted?: () => void;
}

/** Rename or delete a course. Delete is a second, explicit confirmation step. */
export default function CourseSettingsModal({
  subject,
  onClose,
  onDeleted,
}: CourseSettingsModalProps) {
  const updateSubject = useUpdateSubject();
  const deleteSubject = useDeleteSubject();
  const { toast } = useToast();
  const [confirmingDelete, setConfirmingDelete] = useState(false);

  const close = () => {
    setConfirmingDelete(false);
    updateSubject.reset();
    deleteSubject.reset();
    onClose();
  };

  if (!subject) return null;

  if (confirmingDelete) {
    return (
      <Modal
        open
        onClose={close}
        title={`Delete ${subject.name}?`}
        description="Students stay on your roster - they're only removed from this course. This can't be undone."
        footer={
          <>
            <Button variant="secondary" onClick={() => setConfirmingDelete(false)}>
              Cancel
            </Button>
            <Button
              variant="danger"
              disabled={deleteSubject.isPending}
              onClick={() =>
                deleteSubject.mutate(subject.id, {
                  onSuccess: () => {
                    toast(`Deleted ${subject.name}`);
                    close();
                    onDeleted?.();
                  },
                })
              }
            >
              {deleteSubject.isPending ? "Deleting..." : "Delete"}
            </Button>
          </>
        }
      >
        {deleteSubject.isError ? (
          <Alert variant="danger">{getApiErrorMessage(deleteSubject.error)}</Alert>
        ) : null}
      </Modal>
    );
  }

  return (
    <Modal open onClose={close} title="Course settings" description={`Code ${subject.course_code}`}>
      <SubjectForm
        defaultName={subject.name}
        onSubmit={async (values) => {
          await updateSubject.mutateAsync({ id: subject.id, ...values });
          toast("Course renamed");
          close();
        }}
        isSubmitting={updateSubject.isPending}
        error={updateSubject.error}
        submitLabel="Save"
        onCancel={close}
      />
      <div className="mt-6 border-t border-border pt-4">
        <button
          type="button"
          onClick={() => setConfirmingDelete(true)}
          className="text-footnote font-semibold text-danger hover:underline"
        >
          Delete this course…
        </button>
      </div>
    </Modal>
  );
}
