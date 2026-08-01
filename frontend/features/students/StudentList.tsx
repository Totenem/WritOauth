"use client";

import { Card, Spinner } from "@/components";
import { useDeleteStudent, useStudents } from "@/hooks/useStudents";
import type { Student } from "@/types";
import { getApiErrorMessage } from "@/utils/apiError";
import StudentCard from "./StudentCard";

export default function StudentList() {
  const { data: students, isPending, isError, error } = useStudents();
  const deleteStudent = useDeleteStudent();

  const handleDelete = (student: Student) => {
    if (!window.confirm(`Delete "${student.name}"? This cannot be undone.`)) {
      return;
    }
    deleteStudent.mutate(student.id);
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

  if (students.length === 0) {
    return (
      <Card>
        <p className="text-sm text-text-muted">
          No students yet. Add your first student to get started.
        </p>
      </Card>
    );
  }

  return (
    <div className="space-y-3">
      {deleteStudent.isError ? (
        <p role="alert" className="text-sm text-danger">
          {getApiErrorMessage(deleteStudent.error)}
        </p>
      ) : null}

      <ul className="space-y-3">
        {students.map((student) => (
          <li key={student.id}>
            <StudentCard
              student={student}
              onDelete={handleDelete}
              isDeleting={deleteStudent.isPending && deleteStudent.variables === student.id}
            />
          </li>
        ))}
      </ul>
    </div>
  );
}
