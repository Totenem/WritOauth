from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database.connection import get_db
from schemas.paper import BaselinePaperCreate, AnalysisPaperCreate, PaperResponse

router = APIRouter(prefix="/api/papers", tags=["papers"])


@router.post("/baseline", response_model=PaperResponse, status_code=201)
async def upload_baseline(body: BaselinePaperCreate, db: Session = Depends(get_db)) -> dict:
    return {"status": "not_implemented"}


@router.post("/analyze", response_model=PaperResponse, status_code=201)
async def upload_for_analysis(
    body: AnalysisPaperCreate, db: Session = Depends(get_db)
) -> dict:
    return {"status": "not_implemented"}


@router.get("/{paper_id}", response_model=PaperResponse)
async def get_paper(paper_id: int, db: Session = Depends(get_db)) -> dict:
    return {"status": "not_implemented"}
