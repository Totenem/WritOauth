# AI Pipeline Developer Guide

## Overview

The AI pipeline verifies authorship by comparing a new submission against a student's established writing profile. It does NOT detect AI-generated text generically — it checks whether the writing style matches *this specific student*.

## Service Responsibilities

| Service | File | Responsibility |
|---------|------|---------------|
| `FingerprintService` | `ai/fingerprint_service.py` | Extract stylometric features (vocabulary, sentence structure, grammar, readability, punctuation, formatting) |
| `EmbeddingService` | `ai/embedding_service.py` | Vectorize text using `BAAI/bge-small-en-v1.5` (or configured model) |
| `RetrievalService` | `ai/retrieval_service.py` | Query ChromaDB for top-k verified baseline papers for the student |
| `PromptBuilder` | `llm/prompt_builder.py` | Construct the LLM prompt with fingerprint + retrieved samples + new paper |
| `LangChainPipeline` | `llm/langchain_pipeline.py` | Orchestrate the LangChain call to Qwen via Ollama |
| `ScoringService` | `ai/scoring_service.py` | Parse LLM response into structured scores (0–1 per dimension) |
| `ExplanationService` | `ai/explanation_service.py` | Generate natural-language reasoning for the teacher |
| `ProfileEngine` | `ai/profile_engine.py` | Maintain and version the student's writing profile in ChromaDB |
| `AIOrchestrator` | `ai/orchestrator.py` | Coordinate all services in the correct order |

## ChromaDB

ChromaDB stores document embeddings for each student's baseline papers. Each document in ChromaDB is tagged with the `student_id` metadata field so retrieval can filter to the correct student.

Collections: one collection named `student_baselines` with metadata filtering on `student_id`.

## Implementing a Service (Stub → Real)

Each service file currently raises `NotImplementedError`. To implement one:

1. Add the required imports (e.g., `from sentence_transformers import SentenceTransformer`)
2. Initialize the model/client in `__init__`
3. Implement the method body
4. Write a unit test in `backend/tests/test_ai/`

Example for `EmbeddingService`:

```python
from sentence_transformers import SentenceTransformer
from config.settings import get_settings

class EmbeddingService:
    def __init__(self) -> None:
        settings = get_settings()
        self.model = SentenceTransformer(settings.embedding_model)

    def embed(self, content: str) -> list[float]:
        return self.model.encode(content).tolist()
```

## Ollama Setup

Qwen 2.5 runs locally via Ollama. First-time setup:

```bash
docker compose exec ollama ollama pull qwen2.5:1.5b
```

Verify it works:

```bash
docker compose exec ollama ollama run qwen2.5:1.5b "Hello"
```

The `QwenClient` connects to Ollama at `http://ollama:11434` (within Docker) or `http://localhost:11434` (local dev).

## Implementation Checklist (per module)

- [ ] `FingerprintService.extract` — NLP feature extraction
- [ ] `EmbeddingService.embed` — SentenceTransformer vectorization
- [ ] `RetrievalService.retrieve` — ChromaDB query with student_id filter
- [ ] `PromptBuilder.build` — Structured prompt template
- [ ] `QwenClient.infer` — Ollama HTTP call
- [ ] `LangChainPipeline.run` — LangChain chain execution
- [ ] `ScoringService.score` — Parse structured JSON from LLM response
- [ ] `ExplanationService.explain` — Format reasoning for teachers
- [ ] `ProfileEngine.update_profile` — Upsert embeddings to ChromaDB
- [ ] `AIOrchestrator.analyze` — Wire all services together
