.PHONY: up down build migrate lint-backend lint-frontend test-backend test-frontend logs prune prune-all

up:
	docker compose up

down:
	docker compose down

build:
	docker compose build

migrate:
	docker compose exec backend alembic upgrade head

lint-backend:
	docker compose exec backend black --check .
	docker compose exec backend ruff check .
	docker compose exec backend mypy . --ignore-missing-imports

lint-frontend:
	docker compose exec frontend npm run lint
	docker compose exec frontend npm run type-check

test-backend:
	docker compose exec backend pytest tests/ -v

test-frontend:
	docker compose exec frontend npm test

logs:
	docker compose logs -f

# Reclaim disk space safely: stops containers and drops dangling images +
# build cache. Named volumes (mysql_data, chroma_data, ollama_models) are KEPT,
# so your DB, vector store, and pulled models survive. Note the next build
# rebuilds from scratch (slower) since the cache is gone.
prune:
	docker compose down
	docker builder prune -f
	docker image prune -f

# Destructive full reset: also removes named volumes (wipes DB / vector store /
# Ollama models) and every unused image on the machine. Use only for a clean slate.
prune-all:
	docker compose down -v
	docker system prune -af --volumes
