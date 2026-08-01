# Deployment Guide ($0/month)

WritOauth is deployed at zero cost across three free tiers:

| Component | Host | Why |
|-----------|------|-----|
| Backend (FastAPI) | [Render](https://render.com) | Free Docker web service |
| Database (Postgres) | [Neon](https://neon.tech) | Free serverless Postgres, no forced expiry |
| Frontend (Next.js) | [Vercel](https://vercel.com) | Free tier, native Next.js support |

## Why Postgres instead of MySQL

The backend was originally built against MySQL. As part of this deployment
work, it was **migrated from MySQL to Postgres** — a deliberate, approved
stack change, not an accident. The reason: genuinely free, non-expiring MySQL
hosting is hard to find (free tiers on common MySQL hosts are usually
time-limited trials). Neon's free Postgres tier has no forced expiry, which
made Postgres the practical choice for a permanently-free deployment.

The project's one Alembic migration
(`backend/database/migrations/versions/97c81dfca646_initial_schema.py`) only
used portable SQLAlchemy types (`sa.JSON`, `sa.Enum`, standard column types) —
no MySQL-specific types — so the migration carried across cleanly. It was
verified end-to-end against a real local `postgres:16` container
(`alembic upgrade head`), not just read for portability.

## Part A — Already done in this repo

These changes are already merged; nothing further to do for them.

- **Driver swap**: `pymysql` → `psycopg[binary]` in `backend/requirements.txt`.
- **Settings default**: `backend/config/settings.py`'s `database_url` default
  now uses the `postgresql+psycopg://` scheme (still just a local-dev
  fallback — never a real secret, same pattern as before).
- **`docker-compose.yml`**: the `mysql` service was replaced with `postgres:16`
  (env vars, volume, and healthcheck updated to match); the `backend`
  service's `DATABASE_URL` now points at Postgres.
- **`backend/Dockerfile`**:
  - Removed `default-libmysqlclient-dev` from both build stages — no longer
    needed, since `psycopg[binary]` ships prebuilt wheels with no native
    build dependencies. This also shrinks the image and speeds up builds.
  - The runtime `CMD` no longer passes `--reload` (a dev-only filesystem
    watcher with no benefit — only overhead — in a deployed container).
  - The runtime `CMD` now listens on `${PORT:-8000}` via a shell-form CMD
    (not the previous exec-form array), because exec-form `CMD` arrays don't
    expand environment variables — and Render (like most PaaS hosts) injects
    its own `PORT` value that the container must bind to, not a hardcoded
    8000. Local Docker Compose restores `--reload` via a `command:` override
    on the `backend` service, so local hot-reload still works.
- **CORS**: `backend/main.py` no longer hardcodes `allow_origins=["*"]`. It
  reads a new `cors_origins` setting (comma-separated string, parsed via
  `Settings.cors_origins_list`), defaulting to `http://localhost:3000`.
- **`render.yaml`**: a Render Blueprint at the repo root, describing a free
  Docker web service built from `backend/Dockerfile`, with a `/health` health
  check and `sync: false` placeholders for `DATABASE_URL`, `JWT_SECRET_KEY`,
  and `CORS_ORIGINS` (so real values are only ever entered in Render's
  dashboard, never committed).
- **CI/CD**: `.github/workflows/cd.yml` no longer has placeholder
  "configure RAILWAY_TOKEN/RENDER_API_KEY" or "configure BACKEND_URL" steps
  that didn't do anything real. It now only builds and pushes images to GHCR
  for provenance — actual deployment happens via Render's and Vercel's native
  GitHub integrations (connected once in each dashboard), not from CI.
- **Frontend**: no code changes were needed. `frontend/next.config.mjs` has
  `output: "standalone"` (used for the Docker build); Vercel uses its own
  build pipeline and simply ignores this setting, so it's harmless there. No
  `vercel.json` was added — a standard Next.js App Router project needs none.
- Test suite (`conftest.py` and friends) already used SQLite's
  `PRAGMA foreign_keys=ON` for FK enforcement in tests. That workaround is
  still correct regardless of prod DB — Postgres enforces FKs by default too,
  same as MySQL did — so it was kept as-is, with the comment updated to say
  "prod" instead of naming MySQL specifically.

## Part B — One-time manual steps (you need to do these)

These steps happen once, in each provider's dashboard. Nothing here is
committed to the repo.

### 1. Create a Neon Postgres database

1. Sign up / log in at [neon.tech](https://neon.tech).
2. Create a new project (any region close to you or your Render region).
3. From the project dashboard, copy the **connection string** — it looks like
   `postgresql://<user>:<password>@<host>/<dbname>?sslmode=require`.
4. Rewrite the scheme for SQLAlchemy/psycopg:
   `postgresql+psycopg://<user>:<password>@<host>/<dbname>?sslmode=require`.
   Keep this value handy — it's the `DATABASE_URL` for Render (step 2).

### 2. Create the Render web service

Option A — apply the blueprint:

1. In the Render dashboard, choose **New > Blueprint**, connect this GitHub
   repo, and let Render read `render.yaml` from the repo root.

Option B — create manually:

1. **New > Web Service**, connect this repo, runtime **Docker**, Dockerfile
   path `backend/Dockerfile`, root/context `backend/`, plan **Free**.

Either way, once the service exists, set these environment variables in the
Render dashboard (**Environment** tab):

| Key | Value |
|-----|-------|
| `DATABASE_URL` | the Neon connection string from step 1, rewritten to `postgresql+psycopg://...` |
| `JWT_SECRET_KEY` | a freshly generated random secret — see below |
| `CORS_ORIGINS` | your Vercel URL once you have it (step 4), e.g. `https://writoauth.vercel.app` |

To generate a secret for `JWT_SECRET_KEY`:

```bash
openssl rand -hex 32
```

### 3. Run the migration once, against Neon

With `DATABASE_URL` pointed at Neon (either export it locally, or use
Render's shell), run from `backend/`:

```bash
export DATABASE_URL="postgresql+psycopg://<user>:<password>@<host>/<dbname>?sslmode=require"
alembic upgrade head
```

This only needs to be run once (and again for any future migrations). Render
does not run migrations automatically on deploy.

### 4. Create the Vercel project

1. In Vercel, **New Project**, import this repo.
2. Set **Root Directory** to `frontend/`.
3. Set the environment variable `NEXT_PUBLIC_API_URL` to your Render backend's
   public URL (e.g. `https://writoauth-backend.onrender.com`).
4. Deploy. Once you have the Vercel URL, go back to Render and set
   `CORS_ORIGINS` to it (step 2), then redeploy the backend so CORS picks up
   the change.

### Known caveat: Render free-tier cold starts

Render's free web services **sleep after 15 minutes of inactivity**. The
first request after idling takes roughly **30–50 seconds** to wake the
container back up. Keep this in mind before a live demo (e.g. in front of a
teacher) — consider "waking" the backend with a manual health-check request
a minute or two beforehand.
