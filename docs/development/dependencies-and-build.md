# Backend Dependencies & Build Notes

## NLP strategy: in-process spaCy, no LLM and no model server

The authorship engine runs **in the FastAPI process**. There is no Ollama
container, no ChromaDB, no LangChain and no LLM of any kind - earlier
versions of this document described that design, which was never built and
has since been ruled out.

What is actually used:

- **spaCy `en_core_web_sm`** for POS tags, dependency parse and morphology.
- **pyspellchecker** (dependency-free) for dictionary lookups.
- **pyphen** for syllable counts.
- **pypdf** / **python-docx** for document text extraction.

All are pure Python or ship prebuilt wheels. Nothing downloads a model at
runtime: `en_core_web_sm` is pinned in `requirements.txt` as a wheel URL, so
the image is self-contained and works offline.

### Rules for `backend/requirements.txt`

- **Do not** add `torch`, `transformers` or `sentence-transformers`. The
  default `torch` wheel bundles ~2GB of CUDA runtime a CPU-only
  `python:3.11-slim` image cannot use, and it was the main cause of
  multi-thousand-second image builds.
- **Do not** add `textstat`. It pulls in `nltk` plus four transitive
  dependencies, and some of its code paths expect corpora to be
  downloadable at runtime, which breaks the offline guarantee. `pyphen` is
  used directly instead and the readability formulas are implemented in
  `ai/features/discourse.py`.
- **Do not** add `language_tool_python`. It requires a JVM and a ~200MB
  download.
- **Keep `spacy`, `thinc` and `blis` pinned together.** They must all
  resolve to prebuilt wheels on linux aarch64 (for an ARM host such as
  Oracle Ampere). spaCy 3.8.16 pins `thinc>=8.3.12,<8.4.0`, and 8.3.13 is
  the highest release in that range with aarch64 wheels - `thinc`'s own
  latest release publishes none, so an unpinned resolver would drop an ARM
  build into a source compile needing `build-essential`.

`fastembed` and its ONNX runtime were removed along with the embedding-based
scorer. That model was semantic, so it measured what an essay was *about*
rather than who wrote it.

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
  Keeps named volumes (the Postgres data directory). Next build is slower
  since the cache is gone.
- `make prune-all` — destructive: also removes named volumes (wipes the
  database) and all unused images. Clean-slate only.

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
- Vars set via `$GITHUB_ENV` are **job-scoped**. Everything that references the
  image path currently lives in the single `build-and-push` job, so this isn't
  an issue today — but if a new job is ever added that also needs the image
  path, it can't see `IMAGE_REPO` from `build-and-push` and must recompute
  `${GITHUB_REPOSITORY,,}` inline (or the value must be passed via job outputs).
- This matters most for forks under a differently-cased org/user — the pipeline
  stays correct without edits as long as the lowercasing is applied.
- Note: `cd.yml` only builds and pushes images to GHCR for provenance. Actual
  deployment is handled by Render's and Vercel's native GitHub integrations
  (see `docs/development/deployment.md`), not by a job in this workflow.
