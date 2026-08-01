from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from application.services.analysis_service import AnalysisNotFoundError, AnalysisService
from database.connection import get_db
from models.teacher import Teacher
from schemas.analysis import AnalysisResultResponse, FeedbackCreate, FeedbackResponse
from utils.dependencies import get_current_teacher

router = APIRouter(prefix="/api/analysis", tags=["analysis"])


@router.get("/{analysis_id}", response_model=AnalysisResultResponse)
async def get_analysis(
    analysis_id: int,
    db: Session = Depends(get_db),
    _current_teacher: Teacher = Depends(get_current_teacher),
) -> AnalysisResultResponse:
    try:
        return AnalysisService(db).get_analysis(analysis_id)
    except AnalysisNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc


@router.post(
    "/{analysis_id}/feedback", response_model=FeedbackResponse, status_code=201
)
async def submit_feedback(
    analysis_id: int,
    body: FeedbackCreate,
    db: Session = Depends(get_db),
    _current_teacher: Teacher = Depends(get_current_teacher),
) -> FeedbackResponse:
    try:
        return AnalysisService(db).submit_feedback(analysis_id, body)
    except AnalysisNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc
