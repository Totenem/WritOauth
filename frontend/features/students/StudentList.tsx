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
import { useDeleteStudent, useStudents } from "@/hooks/useStudents";
import type { Student } from "@/types";
import { getApiErrorMessage } from "@/utils/apiError";
import StudentCard from "./StudentCard";

export default function StudentList() {
  const { data: students, isPending, isError, error } = useStudents();
  const deleteStudent = useDeleteStudent();

  const { toast } = useToast();
  const [pendingDelete, setPendingDelete] = useState<Student | null>(null);

  const confirmDelete = () => {
    if (!pendingDelete) return;
    const name = pendingDelete.name;
    deleteStudent.mutate(pendingDelete.id, {
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

  if (students.length === 0) {
    return (
      <EmptyState
        title="No students yet"
        description="Add a student, then give the system a few writing samples you know are theirs."
      />
    );
  }

  return (
    <div className="space-y-3">
      {deleteStudent.isError ? (
        <Alert variant="danger">{getApiErrorMessage(deleteStudent.error)}</Alert>
      ) : null}

      <ul className="space-y-3">
        {students.map((student) => (
          <li key={student.id}>
            <StudentCard
              student={student}
              onDelete={setPendingDelete}
              isDeleting={deleteStudent.isPending && deleteStudent.variables === student.id}
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
