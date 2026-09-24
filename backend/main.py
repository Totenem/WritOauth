from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api import analysis, auth, dashboard, papers, students, subjects
from config.settings import get_settings

app = FastAPI(
    title="WritOauth API",
    description="AI-powered authorship verification platform for educators",
    version="0.1.0",
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
