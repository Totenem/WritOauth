# Local Development Setup

## Prerequisites

Install these before starting:

- **Docker Desktop** — [docker.com/products/docker-desktop](https://docker.com/products/docker-desktop)
- **Node.js 20** — [nodejs.org](https://nodejs.org) or via `nvm`
- **Python 3.11** — [python.org](https://python.org) or via `pyenv`

## Environment Variables

Copy the template and fill in values:

```bash
cp .env.example .env
```

| Variable | Default | Notes |
|----------|---------|-------|
| `DATABASE_URL` | `postgresql+psycopg://writoauth:password@postgres:5432/writoauth_db` | Postgres connection string |
| `JWT_SECRET_KEY` | *(change this)* | Sign JWT tokens — use a long random string in prod |
| `JWT_ALGORITHM` | `HS256` | JWT signing algorithm |
| `NEURAL_STYLE_ENABLED` | `true` | Run the LUAR neural authorship model. `false` scores with the six stylometric profiles only |
| `NEURAL_STYLE_MODEL` | `rrivera1849/LUAR-MUD` | Hugging Face model id — see [authorship-models.md](authorship-models.md) |
| `NEURAL_STYLE_REVISION` | `f1db5025…` (pinned) | Reviewed commit of the model repo. Never set to a branch name |
| `ANALYSIS_FLAG_THRESHOLD` | `75.0` | Overall score (0-100) below which a submission is flagged |
| `NEXT_PUBLIC_API_URL` | `http://localhost:8000` | Used by the browser to reach the backend |
| `POSTGRES_USER` | `writoauth` | Application DB user (Docker only) |
| `POSTGRES_PASSWORD` | `password` | Application DB password (Docker only) |
| `POSTGRES_DB` | `writoauth_db` | Database name (Docker only) |

**Note on `NEXT_PUBLIC_API_URL`:** When the browser makes requests, it must use `http://localhost:8000`. When the frontend container talks to the backend container, it uses `http://backend:8000`. These are different — the `docker-compose.yml` sets `NEXT_PUBLIC_API_URL=http://localhost:8000` as a container override, which is correct for a dev setup where the browser accesses the backend through the host.

## Docker Services

```
docker compose up
```

| Service | Port | Description |
|---------|------|-------------|
| `frontend` | 3000 | Next.js dev server (hot reload) |
| `backend` | 8000 | FastAPI with hot reload; runs the authorship engine and LUAR in-process |
| `postgres` | 5432 | Postgres 16 — application database |

Start only the database (for running backend/frontend on the host):

```bash
docker compose up postgres
```

### Hot reload on Windows / macOS

Both services bind-mount their source (`./frontend:/app`, `./backend:/app`),
but file changes on a Windows or macOS host don't send inotify events into
the Linux containers, so file watchers never notice edits. Compose therefore
forces polling:

- frontend: `WATCHPACK_POLLING=true` (Next.js's webpack watcher —
  `CHOKIDAR_USEPOLLING` is the Create-React-App setting and does nothing here)
- backend: `WATCHFILES_FORCE_POLLING=true` (uvicorn `--reload` via watchfiles)

`frontend/.dockerignore` keeps the host's `node_modules`/`.next` out of the
image, since they would bring Windows-native binaries into a Linux container.

**If edits still don't show up** after pulling these changes, the anonymous
`node_modules`/`.next` volumes are still the old ones. Rebuild and recreate
them (this keeps your Postgres data):

```bash
docker compose up --build --renew-anon-volumes
```

Do **not** use `docker compose down -v` for this: `-v` also deletes the named
`postgres_data` volume, which wipes your database.

### The LUAR model (first start)

On the first start the backend downloads the LUAR model (~330 MB) in a
background thread into the `hf_cache` named volume. Later starts reuse it.
A paper uploaded while the model is still loading waits for it to finish.
If loading *fails* (no network, missing torch), papers are scored with the
six stylometric profiles only and the "AI Style Fingerprint" profile shows
as not measured. Check that it loaded with:

```bash
docker compose logs backend | grep "neural style"
```

After enabling the model on a database with existing papers, backfill the
embeddings once:

```bash
docker compose exec backend python -m scripts.rebuild_analysis
```

## Running Database Migrations

After pulling changes that include new migrations:

```bash
make migrate
# or directly:
docker compose exec backend alembic upgrade head
```

To create a new migration after changing a SQLAlchemy model:

```bash
docker compose exec backend alembic revision --autogenerate -m "describe your change"
```

Then review the generated file in `backend/database/migrations/versions/` before committing it.

**Migration `e7b3c5a1f9d2` (unique student names)** merges any existing
duplicate students — same teacher, same first and last name ignoring case and
spacing — into the oldest record before adding the unique index. It prints
which students were merged. Run `python -m scripts.rebuild_analysis`
afterwards so the merged students' profiles include their moved papers. The
merge cannot be undone by `alembic downgrade`.
