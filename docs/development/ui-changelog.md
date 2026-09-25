# UI Changelog

A running log of frontend UI/UX work, kept in sync with what's actually built. Updated after
every UI change — newest entry on top. Not a place for backend or infra changes; see git history
for those.

Each entry: what changed, the files touched, and any decisions or gaps worth remembering (e.g.
"mockup had X, backend doesn't support it, so we did Y instead").

---

## 2026-09-25 — Courses & Baseline Setup (course codes, enrollment, CSV batch upload)

Redesigned `/subjects` into "Courses & Baseline Setup" from the mockup, and added the behaviour
behind it. **This one is full stack** (backend + migration), unlike the earlier UI-only entries.

**Rules now enforced:**
- A teacher must create a course before adding students. `/students` shows "Create a course
  first" (linking to `/subjects`) and hides the add form while the teacher has zero courses; the
  API rejects a student with no `subject_ids` (422) or with another teacher's course (404).
- Every course gets a unique, auto-generated code (e.g. `ENG301-7KQM`, name prefix + 4
  unambiguous characters) that the batch CSV uses.
- Students are enrolled into courses (many-to-many), each enrollment `active` or `inactive`.

**`/subjects` — course grid** (`features/subjects/SubjectList.tsx`, `SubjectCard.tsx`): header
panel with "+ Create New Course Group" (opens a dialog), one card per course with the code,
enrolled-student count, "Baseline Locked Students: X / Y" progress bar, "View Roster", and a gear
that opens `CourseSettingsModal.tsx` (rename, or delete behind a second confirmation). Empty state:
"No courses yet" + "Create your first course".

**`/subjects/[id]` — course roster** (`app/(dashboard)/subjects/[id]/page.tsx`): course code with
copy button and course settings; `BatchUpload.tsx` ("Download Template" gives a CSV with the header
`Subject Code, Last Name, First Name, Email, Status`; the upload shows how many were enrolled and
lists each skipped row with its reason); `CourseRoster.tsx` table (name, email, active/inactive,
baseline x/3 Locked/Collecting).

**Batch upload rules:** a row is skipped (and reported by spreadsheet row number) if its Subject
Code isn't this course's code, first/last name is blank, or Status isn't active/inactive (blank =
active). Every valid row becomes a new student; there's no de-duplication against existing
students. Wrong file type, missing header columns, or a non-UTF-8 file fail the whole upload.

**Students:** `StudentForm.tsx` now has First name / Last name / Email (optional), plus a required
"Enroll in" course checklist when creating (the only course is pre-ticked). `StudentCard.tsx`
shows email and course chips; the detail page edits first/last/email (enrollment isn't edited
there).

**Backend** (`d4e2a9f71c63` migration): `subjects.course_code` (backfilled for existing courses),
`students.name` split into `first_name`/`last_name` (backfill splits on the first space) + nullable
`email`, new `enrollments` table. New endpoints `GET /api/subjects/{id}/roster` and
`POST /api/subjects/{id}/students/batch`. API responses still include a combined `name` for
students, so the dashboard and paper forms needed no changes.

**Deviations from the mockup:** no institution pill (no such data); "Audit Reports" tab still
absent; header keeps separate "Baseline Setup" and "Courses" tabs rather than one combined tab.

**Known issue (existed before, not fixed here):** deleting a course that already has papers
filed under it fails with a server error, because papers can't lose their course. The UI shows a
generic error in that case.

**Files:** backend — `models/enrollment.py` (new), `models/student.py`, `models/subject.py`,
`utils/course_code.py` (new), `application/constants.py` (new),
`application/repositories/{enrollment,student,subject,dashboard}_repository.py`,
`application/services/{student,subject}_service.py`, `schemas/{student,subject}.py`,
`api/{students,subjects}.py`, migration `d4e2a9f71c63_*`. Frontend — `types/{student,subject}.ts`,
`services/subject.service.ts`, `hooks/{useSubjects,useStudents}.ts`,
`features/subjects/{SubjectList,SubjectCard,CourseSettingsModal,BatchUpload,CourseRoster}.tsx`,
`features/students/{StudentForm,StudentCard}.tsx`, `app/(dashboard)/subjects/{page,[id]/page}.tsx`,
`app/(dashboard)/students/{page,[id]/page}.tsx`, `components/icons.tsx` (new icons).

Tests: backend helpers in `tests/helpers.py`; new `test_services/test_subject_roster.py`,
`test_utils/test_course_code.py`, roster/batch API tests in `test_api/test_subjects.py`; student
tests updated for the new fields. Frontend fixtures in `__tests__/fixtures/roster.ts`; subject and
student page/form tests rewritten for the new flows.

---

## 2026-09-25 — Dashboard redesign (light + dark)

Rebuilt the `/dashboard` page and app shell to match the provided mockup, using the new brand
palette. No backend changes.

**Palette tokens** (`app/globals.css`, `tailwind.config.ts`): brand colors `#05102D` (ink),
`#1A2444` (navy), `#2A468B`/`#3D6AC1` (blue), `#FFF7E3` (cream), `#B89343`/`#CDB178`/`#DFCBA7`
(gold) now drive both the light theme (cream/white surfaces) and dark theme (navy/ink surfaces)
via the existing CSS-variable token system. Added a new `accent` token (gold) alongside the
existing `primary`/`bg`/`text`/`border`/`success`/`warning`/`danger` tokens.

**New app header** (`components/AppHeader.tsx`): replaces the old `Navbar` + `Sidebar` (both
deleted). Two-row header: brand mark + theme toggle + user menu (avatar, name, email, logout) on
top; a horizontal tab strip (Overview & Auditing, Student Baseline Roster, Baseline Setup,
Verification Studio, Courses) and a live engine-status dot (polls `GET /health`) below.

**Dashboard content** (`features/dashboard/DashboardOverview.tsx`): added a "Command Center" hero
panel (students enrolled / baseline coverage / pending review) and a "Submissions Queue & Audit
Log" table (student, course, date checked, consistency score, status, "Inspect Audit Report"
link). Kept all existing sections (baseline-readiness warnings, baseline readiness breakdown,
score distribution chart, "needs a closer look" / "consistently themselves" leaderboards) — same
data, restyled.

**Deviations from the mockup** (backend has no data for these):
- No institution/job-title pill — `Teacher` has no such fields; shows email instead.
- No separate "Audit Reports" listing tab — no endpoint for it; reports are reached per-row.
- "False accusations prevented" tile → "Matched baseline" (submissions ≥ threshold) — not a
  computable metric.
- Paper title column → date checked — papers have no title field.
- "Verified Authentic" badge → "Consistent with baseline" — verification is the teacher's own
  decision (`teacher_decision`), shown separately as "You: genuine" / "You: flagged".

**Files:** `components/AppHeader.tsx` (new), `components/icons.tsx` (new, shared inline SVG
icons), `features/dashboard/DashboardOverview.tsx`, `app/(dashboard)/layout.tsx`,
`app/(dashboard)/dashboard/page.tsx`, `app/globals.css`, `tailwind.config.ts`, `app/layout.tsx`
(theme-color meta), `components/Card.tsx` (radius bump to match), `components/Navbar.tsx` /
`components/Sidebar.tsx` (deleted), `components/index.ts`.

Tests updated: `__tests__/features/dashboard/DashboardOverview.test.tsx` (new copy/labels, table
link assertions).

---

## 2026-09-25 — Shared Login / Sign Up card

Reworked `/login` and `/register` so they're two forms inside one persistent page shell, matching
the mockup where only the right-hand card swaps between "Sign In" and "Sign Up" — the header and
marketing panel stay mounted and keep their state (e.g. an open "Sample Report" tab) across the
switch.

**Shared shell** (`features/authentication/AuthShell.tsx`, now `app/(auth)/layout.tsx`): dark
announcement bar, WritOath header/nav, hero copy, a "How It Works" step list (4 clickable steps)
and "Sample Report" tab (preview using the app's real six profile categories — labelled
"Illustrative sample", scores are made up). Reads the active form (`login` vs `register`) from
the URL via `usePathname()` rather than a prop, since both pages now share one layout.

**Shared card pieces** (`features/authentication/AuthCard.tsx`): `AuthCard`, `SubmitButton`,
`FormError`, `OrDivider`, `GoogleButton` — used by both `LoginForm.tsx` and `RegisterForm.tsx` to
avoid duplicating the gold gradient button, divider, and disabled Google button (no OAuth backend
yet, shown for layout parity with a "Soon" badge).

**Icon field** (`features/authentication/AuthField.tsx`): input with a leading icon and, for
password fields, a show/hide toggle. Icons drawn inline in `features/authentication/icons.tsx`
(later moved to `components/icons.tsx` — see dashboard entry above).

**Register form changes:** matches the mockup — Full Name / Academic Email / Password fields, a
required "I agree with the Terms of Use and Academic Integrity Policy" checkbox, no more Confirm
Password field (replaced by the show/hide toggle). "School / Educational Institution" from the
mockup was **left out** — `Teacher` has no such column and adding it needs a migration; flagged
for a follow-up if wanted.

**Files:** `app/(auth)/layout.tsx` (new), `app/(auth)/login/page.tsx`,
`app/(auth)/register/page.tsx`, `features/authentication/AuthShell.tsx` (new),
`features/authentication/AuthCard.tsx` (new), `features/authentication/AuthField.tsx` (new),
`features/authentication/LoginForm.tsx`, `features/authentication/RegisterForm.tsx`,
`tailwind.config.ts` (initial `brand-*` fixed-color tokens, later superseded by the theme-wide
tokens above).

Tests updated: `__tests__/features/authentication/RegisterForm.test.tsx` (new field labels,
terms-checkbox validation, dropped Confirm Password assertions).
