import type { Student, Subject } from "@/types";

export function makeSubject(overrides: Partial<Subject> = {}): Subject {
  return {
    id: 1,
    teacher_id: 1,
    name: "English 101",
    course_code: "ENGLIS-AB12",
    student_count: 0,
    baseline_ready_count: 0,
    created_at: "2024-01-01T00:00:00Z",
    ...overrides,
  };
}

/** Accepts a display `name` and derives first/last from it, like the API does in reverse. */
export function makeStudent(overrides: Partial<Student> = {}): Student {
  const name = overrides.name ?? "Ana Cruz";
  const [first, ...rest] = name.split(" ");
  return {
    id: 1,
    first_name: first,
    last_name: rest.join(" "),
    email: null,
    subjects: [],
    created_at: "2024-01-01T00:00:00Z",
    ...overrides,
    name,
  };
}
