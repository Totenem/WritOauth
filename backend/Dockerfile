FROM python:3.11-slim AS builder

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
# Cache pip downloads across builds (BuildKit is on by default in Compose v2),
# so editing requirements.txt re-uses already-downloaded wheels instead of
# refetching them every build.
RUN --mount=type=cache,target=/root/.cache/pip \
    python -m venv /opt/venv && \
    /opt/venv/bin/pip install --upgrade pip && \
    /opt/venv/bin/pip install -r requirements.txt

FROM python:3.11-slim AS runtime

WORKDIR /app

# psycopg[binary] ships prebuilt wheels, so no native build deps (e.g. a
# libmysqlclient-dev equivalent) are needed in the runtime image.
COPY --from=builder /opt/venv /opt/venv
COPY . .

ENV PATH="/opt/venv/bin:$PATH"

EXPOSE 8000

# Shell-form CMD (not exec-form array) so $PORT is expanded at container
# start - Render (and most PaaS hosts) inject PORT and require the app to
# listen on it rather than a hardcoded port. --reload is dropped here: it's a
# dev-only filesystem watcher with no benefit (and only overhead) in a
# deployed container.
CMD uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}
