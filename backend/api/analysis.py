from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database.connection import get_db
from schemas.analysis import AnalysisResultResponse, FeedbackCreate, FeedbackResponse

router = APIRouter(prefix="/api/analysis", tags=["analysis"])


@router.get("/{analysis_id}", response_model=AnalysisResultResponse)
async def get_analysis(analysis_id: int, db: Session = Depends(get_db)) -> dict:
    return {"status": "not_implemented"}


@router.post("/{analysis_id}/feedback", response_model=FeedbackResponse, status_code=201)
async def submit_feedback(
    analysis_id: int, body: FeedbackCreate, db: Session = Depends(get_db)
) -> dict:
    return {"status": "not_implemented"}
