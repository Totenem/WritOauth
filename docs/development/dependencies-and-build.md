# Backend Dependencies & Build Notes

## ML / LLM strategy: Ollama over in-process torch

The backend delegates **embeddings and LLM inference to the Ollama container**
over HTTP (via `httpx`), and talks to **ChromaDB as an HTTP client**. It does
not run models in-process.

**Why:** the default `torch` wheel bundles ~2GB of CUDA runtime that the
CPU-only `python:3.11-slim` image can't use. Installing it (plus
`transformers` / `sentence-transformers`) was the main cause of the
multi-thousand-second backend image build. As of this writing,
`embedding_service.py`, `qwen_client.py`, `langchain_pipeline.py`, and
`retrieval_service.py` are unimplemented stubs, so nothing depended on those
packages yet.

### Rules for `backend/requirements.txt`

- **Do not** add `torch`, `transformers`, or `sentence-transformers` — use the
  Ollama service for embeddings and inference.
- Use **`chromadb-client`**, not the full `chromadb` package. The backend only
  talks to the Chroma *service* over HTTP; the full package drags in
  `onnxruntime` + native `hnswlib` builds that add minutes to the image build.
- Keep the `chromadb-client` pin in sync with the `chromadb/chroma` image tag
  in `docker-compose.yml` (both currently `0.5.23`) to avoid client/server
  protocol drift.
- If in-process local embeddings are ever genuinely required, install the
  CPU-only wheels instead of the default CUDA ones:
  ```
  pip install --extra-index-url https://download.pytorch.org/whl/cpu \
      torch==2.3.0 sentence-transformers==3.0.1
  ```

## Build speed

- The `pip install` step uses a BuildKit cache mount
  (`--mount=type=cache,target=/root/.cache/pip`), so editing `requirements.txt`
  reuses already-downloaded wheels instead of refetching them.
- `backend/.dockerignore` keeps caches, virtualenvs, and local data out of the
  build context.

## Disk cleanup

`docker compose down` never removes images, build cache, or named volumes, so
disk usage only grows. Use the Makefile targets:

- `make prune` — safe: stops containers, drops dangling images + build cache.
  Keeps named volumes (DB, vector store, Ollama models). Next build is slower
  since the cache is gone.
- `make prune-all` — destructive: also removes named volumes (wipes DB / vector
  store / Ollama models) and all unused images. Clean-slate only.

## CI/CD image tags: GHCR requires lowercase

GitHub Container Registry (and OCI registries generally) reject uppercase in
repository paths, but `${{ github.repository }}` preserves the original casing
(e.g. `Totenem/WritOauth`). Pushing `ghcr.io/Totenem/WritOauth/backend:latest`
fails with `repository name must be lowercase`.

`.github/workflows/cd.yml` handles this by lowercasing once per job:

```yaml
- name: Compute lowercase image repo
  run: echo "IMAGE_REPO=${GITHUB_REPOSITORY,,}" >> "$GITHUB_ENV"
```

and referencing `ghcr.io/${{ env.IMAGE_REPO }}/...` in the tags. Notes:

- `${GITHUB_REPOSITORY,,}` is **bash** lowercase expansion, so the step must run
  on a bash shell (the `ubuntu-latest` default). On `pwsh`/Windows runners it
  won't lowercase — reuse `${{ env.IMAGE_REPO }}` instead of recomputing.
- Vars set via `$GITHUB_ENV` are **job-scoped**. The `deploy` job can't see
  `IMAGE_REPO` from `build-and-push`, so it recomputes `${GITHUB_REPOSITORY,,}`
  inline. Any new job that references the image path must do the same.
- This matters most for forks under a differently-cased org/user — the pipeline
  stays correct without edits as long as the lowercasing is applied.
