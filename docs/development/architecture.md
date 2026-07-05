# Architecture Guide for Developers

## High-Level Request Flow

```
Browser (Next.js page)
  → frontend/services/*.service.ts   (Axios call)
  → FastAPI route (backend/api/)
  → Service (backend/application/services/)
  → Repository (backend/application/repositories/)
  → SQLAlchemy ORM → MySQL
```

For paper analysis, the flow extends into the AI pipeline:

```
PaperService.upload_for_analysis()
  → AnalyzePaperUseCase.execute()
  → AIOrchestrator.analyze()
      → FingerprintService.extract()    (stylometric features)
      → EmbeddingService.embed()        (semantic vector)
      → RetrievalService.retrieve()     (top-k from ChromaDB)
      → PromptBuilder.build()           (constructs LLM prompt)
      → LangChainPipeline.run()         (calls Qwen via Ollama)
      → ScoringService.score()          (parses LLM response)
      → ExplanationService.explain()    (natural language reasoning)
  → AnalysisRepository.save()          (persists to MySQL)
```

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
├── ai/                       ← AI pipeline services (fingerprint, embed, retrieve, score, explain, profile)
├── llm/                      ← LangChain + Qwen integration (pipeline, prompt builder, Ollama client)
└── utils/                    ← Security helpers (JWT, password hash) and FastAPI dependencies
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
