"use client";

import { useState } from "react";

import {
  Alert,
  Button,
  EmptyState,
  Modal,
  SkeletonBar,
  SkeletonGroup,
  useToast,
} from "@/components";
import { useDeleteSubject, useSubjects } from "@/hooks/useSubjects";
import type { Subject } from "@/types";
import { getApiErrorMessage } from "@/utils/apiError";
import SubjectCard from "./SubjectCard";

export default function SubjectList() {
  const { data: subjects, isPending, isError, error } = useSubjects();
  const deleteSubject = useDeleteSubject();

  const { toast } = useToast();
  const [pendingDelete, setPendingDelete] = useState<Subject | null>(null);

  const confirmDelete = () => {
    if (!pendingDelete) return;
    const name = pendingDelete.name;
    deleteSubject.mutate(pendingDelete.id, {
      onSuccess: () => toast(`Deleted ${name}`),
    });
    setPendingDelete(null);
  };

  if (isPending) {
    return (
      <SkeletonGroup className="space-y-3">
        {[0, 1, 2].map((row) => (
          <SkeletonBar key={row} className="h-20 w-full rounded-xl" />
        ))}
      </SkeletonGroup>
    );
  }

  if (isError) {
    return <Alert variant="danger">{getApiErrorMessage(error)}</Alert>;
  }

  if (subjects.length === 0) {
    return (
      <EmptyState
        title="No subjects yet"
        description="Subjects group papers by class or course. Every paper is filed against one."
      />
    );
  }

  return (
    <div className="space-y-3">
      {deleteSubject.isError ? (
        <Alert variant="danger">{getApiErrorMessage(deleteSubject.error)}</Alert>
      ) : null}

      <ul className="space-y-3">
        {subjects.map((subject) => (
          <li key={subject.id}>
            <SubjectCard
              subject={subject}
              onDelete={setPendingDelete}
              isDeleting={deleteSubject.isPending && deleteSubject.variables === subject.id}
            />
          </li>
        ))}
      </ul>

      <Modal
        open={pendingDelete !== null}
        onClose={() => setPendingDelete(null)}
        title={`Delete ${pendingDelete?.name ?? ""}?`}
        description="This also removes their papers and any analyses. It can't be undone."
        footer={
          <>
            <Button variant="secondary" onClick={() => setPendingDelete(null)}>
              Cancel
            </Button>
            <Button variant="danger" onClick={confirmDelete}>
              Delete
            </Button>
          </>
        }
      />
    </div>
  );
}
