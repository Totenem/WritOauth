"use client";

import { Card } from "@/components";
import { SubjectForm, SubjectList } from "@/features/subjects";
import { useCreateSubject } from "@/hooks/useSubjects";

export default function SubjectsPage() {
  const createSubject = useCreateSubject();

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-text">Subjects</h1>
        <p className="mt-1 text-sm text-text-muted">
          The subjects you teach. Only you can see and edit your own subjects.
        </p>
      </div>

      <Card>
        <h2 className="mb-4 text-lg font-medium text-text">Add a subject</h2>
        <SubjectForm
          onSubmit={(values) => createSubject.mutateAsync(values)}
          isSubmitting={createSubject.isPending}
          error={createSubject.error}
          submitLabel="Add subject"
          resetOnSuccess
        />
      </Card>

      <SubjectList />
    </div>
  );
}
