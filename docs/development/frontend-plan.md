# Frontend Implementation Plan (Auth, Students, Subjects, Papers)

## Context

Backend phases 0-4 are complete and merged to `main`: Auth, Students CRUD, Subjects CRUD (teacher-owned), Papers upload/lookup. All fully tested (113 tests) and lint-clean.

The frontend (`frontend/`) is already fully scaffolded — every page, hook, service function, and feature component exists as a file, one-to-one mirroring the backend's domains (auth, students, subjects, papers, analysis) — but every function body is a stub (`throw new Error("not_implemented")`) or a bare placeholder. This plan implements the frontend for the four domains the backend already fully supports.

**Status: all phases in this plan are complete, plus the Analysis UI that was originally deferred.** See the per-phase sections below.

> **Superseded note (kept for history).** This plan originally said:
>
> > *Out of scope for this plan: the Analysis pages (`app/(dashboard)/analysis/[id]/page.tsx`, `features/analysis/*`). The backend's AI pipeline (`backend/ai/*`, `backend/api/analysis.py`) is still fully stubbed and its design isn't settled — building UI against it now would just get thrown away.*
>
> **That no longer applies.** The AI design decision has been made and shipped: the backend AI engine landed in PR #49 (local `fastembed` embeddings + cosine similarity computed in-process, stylometric breakdown, deterministic template explanation — no Ollama server, no vector DB, no hosted LLM). `backend/api/analysis.py` is real and tested. The Analysis UI was therefore built as **Phase 9b** and is described at the end of this document.

## Phase numbering

Backend phases used labels `phase:0-foundation` through `phase:4-papers`. The AI pipeline was the presumed "phase 5" but was deliberately deferred in favor of this frontend work. To avoid renumbering later, this plan claims phase numbers **5-8** for frontend work; the AI pipeline becomes **phase 9** whenever it's scoped.

**Resolved:** phase 9 ended up split across the two halves of the repo — **9a** is the backend AI engine (PR #49) and **9b** is the frontend Analysis + Feedback UI (documented below). Adjust freely if you'd rather use a separate `frontend:*` label scheme instead of continuing the `phase:N` sequence — flagging this as a naming choice, not a fixed decision.

## Cross-cutting decisions (confirm before/while building)

1. **Route protection.** The JWT lives in `localStorage` (see `utils/tokenStorage.ts`), which server-side Next.js middleware can't read. Recommend a client-side guard in `app/(dashboard)/layout.tsx` (check the token on mount, redirect to `/login` via `useRouter` if absent) rather than middleware + cookies. Tradeoff: a brief flash of the dashboard shell before redirect, vs. the larger lift of moving the token to a cookie. Fine to revisit later if that flash bothers you in practice.
2. **Shared API error helper.** FastAPI error responses are `{"detail": "..."}`. Add one small `utils/apiError.ts` helper (`getApiErrorMessage(error: unknown): string`) that pulls `error.response.data.detail` out of an Axios error, falling back to a generic message. Every form (login, student, subject, paper) uses it instead of re-deriving the same unwrap logic four times.
3. **Query key convention.** Use tuple keys namespaced by domain: `["students"]` / `["students", id]`, `["subjects"]` / `["subjects", id]`, `["papers", id]`. Mutations invalidate the relevant list key on success.
4. **TanStack Query provider.** Not wired up anywhere yet. Needs a client component (e.g. `app/providers.tsx`) holding a `QueryClient` instance, wrapped around `{children}` in `app/layout.tsx`.

## Phase 5 — Foundation + Auth — DONE (PR #50)

**Goal:** a teacher can log in, stay logged in across a refresh, get redirected if unauthenticated, and log out.

| File | Change |
|---|---|
| `app/providers.tsx` (new) | `"use client"` component instantiating `QueryClient` + `QueryClientProvider` |
| `app/layout.tsx` | Wrap `{children}` in `<Providers>` |
| `utils/apiError.ts` (new) | `getApiErrorMessage(error: unknown): string` |
| `services/auth.service.ts` | Implement `login()` (POST `/api/auth/login`) and `logout()` (clear token client-side; the backend's `/logout` is a documented no-op for stateless JWT, so no network call needed) |
| `hooks/useAuth.ts` | `useAuth()` returning `{ login, isLoggingIn, loginError, logout, isAuthenticated }`, backed by a `useMutation` for login and `tokenStorage` for persistence |
| `features/authentication/LoginForm.tsx` | `react-hook-form` form (email/password) using `Input`/`Button`; on submit calls `useAuth().login`, shows `getApiErrorMessage` on 401, redirects to `/dashboard` on success via `useRouter` |
| `app/(auth)/login/page.tsx` | Renders `<LoginForm />` |
| `app/(dashboard)/layout.tsx` | Client-side auth guard (redirect to `/login` if no token) + wire real `Sidebar`/`Navbar` nav links (Students/Subjects/Papers/Logout) — keep this thin, don't redesign `Sidebar`/`Navbar` beyond making the links real |

**Tests:** `__tests__/hooks/useAuth.test.ts` (mock the service module — successful login persists token + flips `isAuthenticated`; failed login surfaces the error, doesn't persist a token), `__tests__/components` for `LoginForm` (valid submit calls `login` and redirects; invalid submit shows an error message and does not redirect).

**Acceptance:**
- Valid login → token saved, redirected to `/dashboard`.
- Invalid login → generic error shown (matches backend's generic "invalid credentials" message; don't leak whether the email exists), no redirect.
- Visiting any `/dashboard/*` route without a token → redirected to `/login`.
- Logout clears the token and redirects to `/login`.

## Phase 6 — Students CRUD UI — DONE (PR #51, closes #43/#44)

Shared roster, no ownership dimension (matches backend Phase 2) — any authenticated teacher sees the same list.

| File | Change |
|---|---|
| `services/student.service.ts` | Implement all 5 functions against `/api/students` |
| `hooks/useStudents.ts` | `useStudents()` (list, `useQuery`), `useStudent(id)` (detail), plus `useCreateStudent`/`useUpdateStudent`/`useDeleteStudent` mutations that invalidate `["students"]` |
| `features/students/StudentList.tsx` | Renders `StudentCard` per student, loading (`Spinner`) and empty states |
| `features/students/StudentCard.tsx` | Name + link to `/students/[id]` |
| `features/students/StudentForm.tsx` | Create/edit form (name field), used both inline on the list page and on the detail page for editing |
| `app/(dashboard)/students/page.tsx` | `StudentList` + a "new student" `StudentForm` |
| `app/(dashboard)/students/[id]/page.tsx` | Detail view, edit `StudentForm`, delete button with confirmation |

**Acceptance:** full CRUD lifecycle works end-to-end against the real API; unknown id shows a not-found state instead of crashing; loading/error states are visible, not blank screens.

## Phase 7 — Subjects CRUD UI — DONE (PR #53, closes #45/#46)

Same shape as Phase 6, but teacher-owned (backend Phase 3) — `GET /api/subjects` already scopes to the current teacher server-side, and a cross-teacher subject returns 404. No extra ownership logic needed client-side; a 404 on `/subjects/[id]` (whether truly missing or someone else's) should render the same generic not-found state.

| File | Change |
|---|---|
| `services/subject.service.ts` | Implement all 5 functions against `/api/subjects` |
| `hooks/useSubjects.ts` | `useSubjects()`, `useSubject(id)`, `useCreateSubject`/`useUpdateSubject`/`useDeleteSubject` |
| `features/subjects/SubjectList.tsx`, `SubjectCard.tsx`, `SubjectForm.tsx` | Same pattern as Students |
| `app/(dashboard)/subjects/page.tsx`, `app/(dashboard)/subjects/[id]/page.tsx` | Same pattern as Students |

**Acceptance:** same as Phase 6; additionally, a 404 (whether not-found or another teacher's subject) renders a clean not-found state rather than an unhandled error.

## Phase 8 — Papers Upload + Detail UI — DONE (PR #54, closes #47/#48)

Depends on Phases 6-7 (upload forms need student/subject pickers). No ownership check server-side (matches backend Phase 4) — any authenticated teacher can upload for any student/subject.

| File | Change |
|---|---|
| `services/paper.service.ts` | Implement `uploadBaseline`, `uploadForAnalysis`, `getPaper` |
| `hooks/usePapers.ts` | `usePaper(id)` (exists, wire it up), add `useUploadBaseline`/`useUploadForAnalysis` mutations |
| `features/papers/BaselineUploadForm.tsx` | Student + subject `<select>` (populated via `useStudents`/`useSubjects`), content textarea. **Deviation:** on success it shows a confirmation with a link to `/papers/[id]` rather than navigating away — teachers usually upload several baselines in a row, so staying put (with the pickers still set) beats bouncing to a detail page each time |
| `features/papers/AnalysisUploadForm.tsx` | Same shape, posts to `/api/papers/analyze`. Navigates to `/analysis/{analysis_id}` on success when one was produced |
| `features/papers/PaperUploadForm.tsx` (new) | The shared body of both upload forms — they differ only in mutation and success handling |
| `features/papers/PaperDetail.tsx` | Shows type (`Badge`), student, subject. ~~For `type: "submission"` papers, show a plain "Analysis pending" note rather than building any analysis UI — out of scope until the AI pipeline lands~~ — **superseded:** the AI pipeline landed, so a scored submission links to `/analysis/{analysis_id}` instead. A submission with a null `analysis_id` (no baseline existed yet) explains that, rather than linking nowhere |
| `app/(dashboard)/papers/baseline/page.tsx`, `papers/analyze/page.tsx`, `papers/[id]/page.tsx` | Wire up the corresponding feature components |

**Acceptance:** uploading a baseline/submission with a valid student+subject succeeds and navigates to the paper detail page; the type badge matches what was uploaded; a backend 400 (shouldn't normally be reachable through the dropdowns, but handle it) shows an error via `getApiErrorMessage` instead of crashing; unknown paper id shows a not-found state.

## Phase 9b — Analysis Results + Feedback UI — DONE

Not in the original plan (it was the deferred "Analysis pages" scope). Built once the backend AI engine landed in PR #49.

| File | Change |
|---|---|
| `services/analysis.service.ts` | `getAnalysis(id)`, `submitFeedback(analysisId, payload)` |
| `hooks/useAnalysis.ts` | `useAnalysis(id)` query (key `["analysis", id]`), `useSubmitFeedback(analysisId)` mutation |
| `features/analysis/ScoreBreakdown.tsx` | The five stylometric scores as labelled meters |
| `features/analysis/AnalysisReport.tsx` | Consistency score, explanation, breakdown, baseline strength, feedback form |
| `features/analysis/FeedbackForm.tsx` | `genuine`/`flagged` radios + optional remarks, with a recorded-decision state |
| `app/(dashboard)/analysis/[id]/page.tsx` | Renders `<AnalysisReport />` |
| `components/Select.tsx`, `components/Textarea.tsx` | Added in Phase 8, reused here |

**Presentation decisions that matter, because they're easy to get wrong:**

1. **No AI verdict badge.** The API returns no `flagged` boolean and no threshold field. `settings.analysis_flag_threshold` is used *only* to compose the `explanation` sentence (`backend/ai/orchestrator.py`) — nothing persists a flag. So the UI shows the backend's own `explanation` as the verdict text rather than recomputing one from a hardcoded 75. The only genuine/flagged state in the product is the **teacher's** recorded feedback decision, which is real data.
2. **The API mixes numeric scales.** `consistency_score` and all five `breakdown` values are **0-100**; `confidence_level` is **0-1**. The pre-existing `formatScore()` multiplies by 100, so it is correct only for `confidence_level`. `formatPercentage()` was added for the 0-100 values — using the wrong one renders a 97.7 score as "9770.0%". Both are covered by tests.
3. **`confidence_level` is not model confidence.** It is `min(1.0, baseline_paper_count / 3)` (`backend/ai/profile_engine.py`). Labelling it "AI confidence" would misrepresent it, so it renders as **"Baseline strength"** with an explicit note that it measures evidence behind the comparison, not suspicion.
4. **Breakdown bars are a single neutral colour.** There is no per-category threshold server-side, so colouring them good/bad would invent a judgement the backend never made.

**Known gap worth a follow-up:** `grammar` and `readability` are documented stylometric proxies (word-length consistency, and a sentence+word-length composite) rather than a real grammar checker or syllable-based readability model — see the Phase 9a notes. The UI presents them under plain labels; if that overstates them for teachers, the fix belongs in the backend or in per-category help text.

## Branching / PR convention

Same as backend: one branch + one PR per phase, off `develop`, e.g. `add/frontend-auth`, `add/frontend-students`, `add/frontend-subjects`, `add/frontend-papers`. PR body lists every issue the phase closes.

## Suggested GitHub issues (mirroring the backend's `N.M` numbering style)

Not created yet — proposing the breakdown here first so you can adjust before they're filed:

- **5.1** Wire TanStack Query provider + shared API error helper
- **5.2** Implement `AuthService` + `useAuth`, build `LoginForm`
- **5.3** Dashboard layout auth guard + real nav
- **6.1** Students service + hooks
- **6.2** Students list/detail/form UI
- **7.1** Subjects service + hooks
- **7.2** Subjects list/detail/form UI
- **8.1** Papers service + hooks
- **8.2** Papers upload forms + detail UI

Let me know if you want these filed as issues on the project board (with a `phase:5-frontend-auth` etc. label set, mirroring the backend convention) before I start building, or if you'd rather I just start on Phase 5 directly.
