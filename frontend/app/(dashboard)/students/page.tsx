"use client";

import { Alert, Card, EmptyState, SkeletonBar, SkeletonGroup } from "@/components";
import { StudentForm, StudentList } from "@/features/students";
import { useCreateStudent } from "@/hooks/useStudents";
import { useSubjects } from "@/hooks/useSubjects";
import type { CreateStudentRequest } from "@/types";
import { getApiErrorMessage } from "@/utils/apiError";

export default function StudentsPage() {
  const createStudent = useCreateStudent();
  const subjects = useSubjects();

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-title2 font-extrabold tracking-tight text-text">Students</h1>
        <p className="mt-1 text-footnote text-text-muted">
          Everyone enrolled in your courses. To add a whole class at once, use a course&apos;s
          batch upload.
        </p>
      </div>

      {subjects.isPending ? (
        <SkeletonGroup>
          <SkeletonBar className="h-40 w-full rounded-2xl" />
        </SkeletonGroup>
      ) : subjects.isError ? (
        <Alert variant="danger">{getApiErrorMessage(subjects.error)}</Alert>
      ) : subjects.data.length === 0 ? (
        // Students always belong to a course, so a new account starts by creating one.
        <EmptyState
          title="Create a course first"
          description="Students are enrolled into courses. Create your first course, then add students to it one by one or in bulk with its course code."
          actionLabel="Go to Courses"
          actionHref="/subjects"
        />
      ) : (
        <Card>
          <h2 className="mb-4 text-headline font-bold text-text">Add a student</h2>
          <StudentForm
            subjects={subjects.data}
            onSubmit={(values) => createStudent.mutateAsync(values as CreateStudentRequest)}
            isSubmitting={createStudent.isPending}
            error={createStudent.error}
            submitLabel="Add student"
            resetOnSuccess
          />
        </Card>
      )}

      <StudentList />
    </div>
  );
}
