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
