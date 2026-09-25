"use client";

import { useState } from "react";

import {
  Alert,
  EmptyState,
  Modal,
  SkeletonBar,
  SkeletonGroup,
  useToast,
} from "@/components";
import { BookIcon, PlusIcon } from "@/components/icons";
import { useCreateSubject, useSubjects } from "@/hooks/useSubjects";
import type { Subject } from "@/types";
import { getApiErrorMessage } from "@/utils/apiError";
import CourseSettingsModal from "./CourseSettingsModal";
import SubjectCard from "./SubjectCard";
import SubjectForm from "./SubjectForm";

export default function SubjectList() {
  const { data: subjects, isPending, isError, error } = useSubjects();
  const [creating, setCreating] = useState(false);
  const [managing, setManaging] = useState<Subject | null>(null);

  return (
    <div className="space-y-6">
      <section className="flex flex-wrap items-center justify-between gap-4 rounded-2xl border border-border bg-bg-elevated p-5 shadow-card sm:p-6">
        <div>
          <h1 className="flex items-center gap-2 text-title3 font-extrabold tracking-tight text-text">
            <BookIcon className="h-5 w-5 text-primary-600" />
            Active Courses &amp; Baseline Collection Policies
          </h1>
          <p className="mt-1 text-footnote text-text-muted">
            Create a course first, then enroll students with its course code.
          </p>
        </div>
        <button
          type="button"
          onClick={() => setCreating(true)}
          className="inline-flex items-center gap-1.5 rounded-lg bg-primary-600 px-4 py-2.5 text-footnote font-semibold text-white transition-colors duration-200 ease-apple hover:bg-primary-700"
        >
          <PlusIcon className="h-4 w-4" />
          Create New Course Group
        </button>
      </section>

      {isPending ? (
        <SkeletonGroup className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
          {[0, 1, 2].map((card) => (
            <SkeletonBar key={card} className="h-44 w-full rounded-2xl" />
          ))}
        </SkeletonGroup>
      ) : isError ? (
        <Alert variant="danger">{getApiErrorMessage(error)}</Alert>
      ) : subjects.length === 0 ? (
        <EmptyState
          title="No courses yet"
          description="Every student belongs to a course, so start here. Each course gets a unique code you'll use to enroll students in bulk."
          actionLabel="Create your first course"
          onAction={() => setCreating(true)}
        />
      ) : (
        <ul className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
          {subjects.map((subject) => (
            <li key={subject.id}>
              <SubjectCard subject={subject} onManage={setManaging} />
            </li>
          ))}
        </ul>
      )}

      <CreateCourseModal open={creating} onClose={() => setCreating(false)} />
      <CourseSettingsModal subject={managing} onClose={() => setManaging(null)} />
    </div>
  );
}

function CreateCourseModal({ open, onClose }: { open: boolean; onClose: () => void }) {
  const createSubject = useCreateSubject();
  const { toast } = useToast();

  const close = () => {
    createSubject.reset();
    onClose();
  };

  return (
    <Modal
      open={open}
      onClose={close}
      title="Create a course"
      description="A unique course code is generated automatically."
    >
      <SubjectForm
        onSubmit={async (values) => {
          const subject = await createSubject.mutateAsync(values);
          toast(`Created ${subject.name} · code ${subject.course_code}`);
          close();
        }}
        isSubmitting={createSubject.isPending}
        error={createSubject.error}
        submitLabel="Create course"
        onCancel={close}
      />
    </Modal>
  );
}

