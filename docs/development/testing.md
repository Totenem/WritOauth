# Testing Guide

## Backend Tests

Run all backend tests:

```bash
# Via Docker
make test-backend

# Locally (from backend/)
pytest tests/ -v
```

Run only AI module tests:

```bash
pytest tests/test_ai/ -v
```

### Environment for Tests

CI sets `DATABASE_URL=sqlite:///./test.db` so tests don't need a running MySQL instance. The SQLite URL is compatible with SQLAlchemy's sync engine.

### Test File Conventions

| What you're testing | Where to put it |
|--------------------|----------------|
| API endpoints | `backend/tests/test_<route>.py` |
| AI services | `backend/tests/test_ai/test_<service>.py` |
| Repositories | `backend/tests/test_repositories/test_<model>_repository.py` |
| Utilities | `backend/tests/test_utils/test_<util>.py` |

### Stub Tests Pattern

Currently, tests for un-implemented services assert `NotImplementedError`:

```python
def test_analyze_raises_not_implemented() -> None:
    orchestrator = _make_orchestrator()
    with pytest.raises(NotImplementedError):
        orchestrator.analyze("text", student_id=1)
```

When you implement a service, replace the `NotImplementedError` test with a real assertion.

## Frontend Tests

Run all frontend tests:

```bash
# Via Docker
make test-frontend

# Locally (from frontend/)
npm test

# Watch mode
npm run test:watch
```

### Test File Conventions

| What you're testing | Where to put it |
|--------------------|----------------|
| Components | `frontend/__tests__/components/<Component>.test.tsx` |
| Utilities | `frontend/__tests__/utils/<util>.test.ts` |
| Hooks | `frontend/__tests__/hooks/<hook>.test.ts` |
| Services | `frontend/__tests__/services/<service>.test.ts` |

### Testing Library

Tests use [Vitest](https://vitest.dev) with [Testing Library](https://testing-library.com/docs/react-testing-library/intro/). The setup file at `frontend/vitest.setup.ts` imports `@testing-library/jest-dom` matchers.

## CI Pipeline

The CI workflow (`.github/workflows/ci.yml`) runs these checks on every PR:

1. `lint-backend` — Black format check, Ruff lint, MyPy type check
2. `lint-frontend` — ESLint, TypeScript `tsc --noEmit`
3. `test-backend` — Pytest (depends on lint passing)
4. `test-frontend` — Vitest (depends on lint passing)
5. `test-ai` — Pytest AI module tests (depends on backend tests)
6. `docker-build` — Builds both Docker images (depends on both test jobs)
7. `security-scan` — Trivy filesystem scan (non-blocking until pre-launch)

PRs **cannot merge** until all jobs pass.
