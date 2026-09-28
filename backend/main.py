import logging
import threading
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from ai.neural_style_service import get_neural_style_service
from api import analysis, auth, dashboard, papers, students, subjects
from config.settings import get_settings


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    # Load the LUAR model in the background at startup so the first paper
    # upload doesn't pay the load (and first-run download). A daemon thread
    # so a slow download never blocks startup or shutdown; `available`
    # is a no-op when the model is disabled.
    #
    # uvicorn configures only its own loggers; without a root handler the
    # app's INFO lines (e.g. "Loaded neural style model ...") are dropped.
    # basicConfig is a no-op if something already configured logging.
    logging.basicConfig(level=logging.INFO, format="%(levelname)s:  %(message)s")
    if get_settings().neural_style_enabled:
        threading.Thread(
            target=lambda: get_neural_style_service().available,
            name="neural-style-warmup",
            daemon=True,
        ).start()
    yield


app = FastAPI(
    title="WritOauth API",
    description="AI-powered authorship verification platform for educators",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_settings().cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(students.router)
app.include_router(subjects.router)
app.include_router(papers.router)
app.include_router(analysis.router)
app.include_router(dashboard.router)


@app.get("/health", tags=["health"])
async def health() -> dict:
    return {"status": "ok"}
