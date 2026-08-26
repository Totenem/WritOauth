"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { Button, Card, Spinner } from "@/components";
import { SubjectForm } from "@/features/subjects";
import { useDeleteSubject, useSubject, useUpdateSubject } from "@/hooks/useSubjects";
import { getApiErrorMessage } from "@/utils/apiError";
import { formatDate } from "@/utils/formatters";

export default function SubjectDetailPage({ params }: { params: { id: string } }) {
  const router = useRouter();
  const subjectId = Number(params.id);

  const { data: subject, isPending, isError, error } = useSubject(subjectId);
  const updateSubject = useUpdateSubject();
  const deleteSubject = useDeleteSubject();

  const handleDelete = () => {
    if (!subject) return;
    if (!window.confirm(`Delete "${subject.name}"? This cannot be undone.`)) {
      return;
    }
    deleteSubject.mutate(subject.id, {
      onSuccess: () => router.push("/subjects"),
    });
  };

  if (!Number.isFinite(subjectId)) {
    return <NotFound />;
  }

  if (isPending) {
    return (
      <div className="flex justify-center py-8">
        <Spinner />
      </div>
    );
  }

  // A subject belonging to another teacher also lands here: the backend returns a
  // plain 404 rather than a 403, deliberately, so it isn't distinguishable from
  // a subject that never existed. One generic state covers both.
  if (isError) {
    return <NotFound message={getApiErrorMessage(error)} />;
  }

  return (
    <div className="space-y-6">
      <div>
        <Link href="/subjects" className="text-sm text-primary-700 hover:underline">
          &larr; Back to subjects
        </Link>
        <h1 className="mt-2 text-2xl font-semibold text-text">{subject.name}</h1>
        <p className="mt-1 text-sm text-text-muted">
          Added {formatDate(subject.created_at)}
        </p>
      </div>

      <Card>
        <h2 className="mb-4 text-lg font-medium text-text">Edit subject</h2>
        <SubjectForm
          defaultName={subject.name}
          onSubmit={(values) => updateSubject.mutateAsync({ id: subject.id, ...values })}
          isSubmitting={updateSubject.isPending}
          error={updateSubject.error}
          submitLabel="Save changes"
        />
      </Card>

      <Card>
        <h2 className="mb-2 text-lg font-medium text-text">Danger zone</h2>
        <p className="mb-4 text-sm text-text-muted">
          Deleting a subject removes it from your subject list.
        </p>
        {deleteSubject.isError ? (
          <p role="alert" className="mb-3 text-sm text-danger">
            {getApiErrorMessage(deleteSubject.error)}
          </p>
        ) : null}
        <Button variant="danger" onClick={handleDelete} disabled={deleteSubject.isPending}>
          {deleteSubject.isPending ? "Deleting..." : "Delete subject"}
        </Button>
      </Card>
    </div>
  );
}

function NotFound({ message }: { message?: string }) {
  return (
    <Card>
      <h1 className="text-lg font-medium text-text">Subject not found</h1>
      <p className="mt-1 text-sm text-text-muted">
        {message ?? "That subject does not exist, or it belongs to another teacher."}
      </p>
      <Link
        href="/subjects"
        className="mt-4 inline-block text-sm text-primary-700 hover:underline"
      >
        &larr; Back to subjects
      </Link>
    </Card>
  );
}
