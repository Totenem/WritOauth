"use client";

import { Card } from "@/components";
import { StudentForm, StudentList } from "@/features/students";
import { useCreateStudent } from "@/hooks/useStudents";

export default function StudentsPage() {
  const createStudent = useCreateStudent();

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-text">Students</h1>
        <p className="mt-1 text-sm text-text-muted">
          The shared roster of students you can upload writing samples for.
        </p>
      </div>

      <Card>
        <h2 className="mb-4 text-lg font-medium text-text">Add a student</h2>
        <StudentForm
          onSubmit={(values) => createStudent.mutateAsync(values)}
          isSubmitting={createStudent.isPending}
          error={createStudent.error}
          submitLabel="Add student"
          resetOnSuccess
        />
      </Card>

      <StudentList />
    </div>
  );
}
