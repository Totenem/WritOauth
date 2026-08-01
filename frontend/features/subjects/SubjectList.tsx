"use client";

import { Card, Spinner } from "@/components";
import { useDeleteSubject, useSubjects } from "@/hooks/useSubjects";
import type { Subject } from "@/types";
import { getApiErrorMessage } from "@/utils/apiError";
import SubjectCard from "./SubjectCard";

export default function SubjectList() {
  const { data: subjects, isPending, isError, error } = useSubjects();
  const deleteSubject = useDeleteSubject();

  const handleDelete = (subject: Subject) => {
    if (!window.confirm(`Delete "${subject.name}"? This cannot be undone.`)) {
      return;
    }
    deleteSubject.mutate(subject.id);
  };

  if (isPending) {
    return (
      <div className="flex justify-center py-8">
        <Spinner />
      </div>
    );
  }

  if (isError) {
    return (
      <Card>
        <p role="alert" className="text-sm text-danger">
          {getApiErrorMessage(error)}
        </p>
      </Card>
    );
  }

  if (subjects.length === 0) {
    return (
      <Card>
        <p className="text-sm text-text-muted">
          No subjects yet. Add your first subject to get started.
        </p>
      </Card>
    );
  }

  return (
    <div className="space-y-3">
      {deleteSubject.isError ? (
        <p role="alert" className="text-sm text-danger">
          {getApiErrorMessage(deleteSubject.error)}
        </p>
      ) : null}

      <ul className="space-y-3">
        {subjects.map((subject) => (
          <li key={subject.id}>
            <SubjectCard
              subject={subject}
              onDelete={handleDelete}
              isDeleting={deleteSubject.isPending && deleteSubject.variables === subject.id}
            />
          </li>
        ))}
      </ul>
    </div>
  );
}
