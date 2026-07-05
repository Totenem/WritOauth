from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api import auth, students, subjects, papers, analysis

app = FastAPI(
    title="WritOauth API",
    description="AI-powered authorship verification platform for educators",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(students.router)
app.include_router(subjects.router)
app.include_router(papers.router)
app.include_router(analysis.router)


@app.get("/health", tags=["health"])
async def health() -> dict:
    return {"status": "ok"}
