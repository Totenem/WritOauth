"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { Button, Card, Spinner } from "@/components";
import { StudentForm } from "@/features/students";
import { useDeleteStudent, useStudent, useUpdateStudent } from "@/hooks/useStudents";
import { getApiErrorMessage } from "@/utils/apiError";
import { formatDate } from "@/utils/formatters";

export default function StudentDetailPage({ params }: { params: { id: string } }) {
  const router = useRouter();
  const studentId = Number(params.id);

  const { data: student, isPending, isError, error } = useStudent(studentId);
  const updateStudent = useUpdateStudent();
  const deleteStudent = useDeleteStudent();

  const handleDelete = () => {
    if (!student) return;
    if (!window.confirm(`Delete "${student.name}"? This cannot be undone.`)) {
      return;
    }
    deleteStudent.mutate(student.id, {
      onSuccess: () => router.push("/students"),
    });
  };

  if (!Number.isFinite(studentId)) {
    return <NotFound />;
  }

  if (isPending) {
    return (
      <div className="flex justify-center py-8">
        <Spinner />
      </div>
    );
  }

  if (isError) {
    return <NotFound message={getApiErrorMessage(error)} />;
  }

  return (
    <div className="space-y-6">
      <div>
        <Link href="/students" className="text-sm text-primary-700 hover:underline">
          &larr; Back to students
        </Link>
        <h1 className="mt-2 text-2xl font-semibold text-text">{student.name}</h1>
        <p className="mt-1 text-sm text-text-muted">
          Added {formatDate(student.created_at)}
        </p>
      </div>

      <Card>
        <h2 className="mb-4 text-lg font-medium text-text">Edit student</h2>
        <StudentForm
          defaultName={student.name}
          onSubmit={(values) => updateStudent.mutateAsync({ id: student.id, ...values })}
          isSubmitting={updateStudent.isPending}
          error={updateStudent.error}
          submitLabel="Save changes"
        />
      </Card>

      <Card>
        <h2 className="mb-2 text-lg font-medium text-text">Danger zone</h2>
        <p className="mb-4 text-sm text-text-muted">
          Deleting a student removes them from the roster.
        </p>
        {deleteStudent.isError ? (
          <p role="alert" className="mb-3 text-sm text-danger">
            {getApiErrorMessage(deleteStudent.error)}
          </p>
        ) : null}
        <Button variant="danger" onClick={handleDelete} disabled={deleteStudent.isPending}>
          {deleteStudent.isPending ? "Deleting..." : "Delete student"}
        </Button>
      </Card>
    </div>
  );
}

function NotFound({ message }: { message?: string }) {
  return (
    <Card>
      <h1 className="text-lg font-medium text-text">Student not found</h1>
      <p className="mt-1 text-sm text-text-muted">
        {message ?? "That student does not exist."}
      </p>
      <Link
        href="/students"
        className="mt-4 inline-block text-sm text-primary-700 hover:underline"
      >
        &larr; Back to students
      </Link>
    </Card>
  );
}
