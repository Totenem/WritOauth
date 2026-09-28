# Architecture Guide for Developers

## High-Level Request Flow

```
Browser (Next.js page)
  → frontend/services/*.service.ts   (Axios call)
  → FastAPI route (backend/api/)
  → Service (backend/application/services/)
  → Repository (backend/application/repositories/)
  → SQLAlchemy ORM → Postgres
```

For paper analysis, the flow extends into the AI pipeline:

```
PaperService.upload_for_analysis()
  → AIOrchestrator.analyze_submission()
      → RetrievalService.retrieve()        (student's latest BaselineProfile, from Postgres)
      → FingerprintService.extract()       (~40 stylometric features, six profiles - spaCy)
      → NeuralStyleService.embed()         (512-d LUAR authorship vector - torch, CPU)
      → ScoringService.score()             (z-scores vs. the student's own spread → 0-100)
      → ExplanationService.explain()       (deterministic template, names the top drivers)
  → AnalysisRepository.save()             (persists to Postgres)

PaperService.upload_baseline()
  → AIOrchestrator.process_baseline()
      → FingerprintService.extract() + NeuralStyleService.embed()
      → ProfileEngine.update_profile()     (new versioned BaselineProfile: stats + LUAR centroid)
```

There is no generative LLM, no vector database and no model server: everything
runs in the FastAPI process. See [ai-pipeline.md](ai-pipeline.md) for the
stylometric engine and [authorship-models.md](authorship-models.md) for LUAR.

## Backend Folder Map

```
backend/
├── main.py                   ← FastAPI app entry point; all routers registered here
├── config/settings.py        ← All env vars via pydantic-settings; import with get_settings()
├── database/
│   ├── connection.py         ← SQLAlchemy engine + get_db() dependency
│   └── migrations/           ← Alembic migration scripts
├── models/                   ← SQLAlchemy ORM models (one file per table)
├── schemas/                  ← Pydantic request/response models (one file per domain)
├── api/                      ← FastAPI APIRouter per domain (auth, students, subjects, papers, analysis)
├── application/
│   ├── repositories/         ← Database queries (one class per model)
│   ├── services/             ← Business orchestration (calls repositories + AI)
│   └── use_cases/            ← One use case per major workflow
├── ai/                       ← Authorship engine: fingerprint (features/), neural_style_service (LUAR),
│                               profile_engine, retrieval, scoring, statistics, explanation, orchestrator
├── scripts/rebuild_analysis.py ← Recomputes all derived data (features, embeddings, profiles, scores)
└── utils/                    ← Security helpers (JWT, password hash), name normalization, FastAPI deps
```

## Adding a New API Endpoint

1. **Schema** — add request/response Pydantic models to `backend/schemas/<domain>.py`
2. **Repository** — add a query method to `backend/application/repositories/<domain>_repository.py`
3. **Service** — add a service method that calls the repository
4. **Route** — add the decorated endpoint to `backend/api/<domain>.py`
5. **Register** — if you created a new router file, include it in `backend/main.py`

## Frontend Folder Map

```
frontend/
├── app/                      ← Next.js App Router pages
│   ├── (auth)/               ← Unauthenticated routes (login)
│   └── (dashboard)/          ← Authenticated routes with sidebar layout
├── types/                    ← TypeScript interfaces (mirrors backend schemas)
├── services/                 ← Axios API client functions (one file per domain)
├── hooks/                    ← TanStack Query hooks wrapping services
├── features/                 ← React feature modules (authentication, students, subjects, papers, analysis)
├── components/               ← Shared UI primitives (Button, Input, Card, etc.)
└── utils/                    ← Token storage, formatters
```

## Adding a New Frontend Feature

1. **Type** — add interfaces to `frontend/types/<domain>.ts`
2. **Service** — add async functions to `frontend/services/<domain>.service.ts`
3. **Hook** — create a TanStack Query hook in `frontend/hooks/use<Domain>.ts`
4. **Feature component** — build the UI in `frontend/features/<domain>/`
5. **Page** — wire the feature component into the appropriate `frontend/app/(dashboard)/<route>/page.tsx`
