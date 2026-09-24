from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from application.services.analysis_service import (
    AnalysisForbiddenError,
    AnalysisNotFoundError,
    AnalysisService,
)
from database.connection import get_db
from models.teacher import Teacher
from schemas.analysis import AnalysisResultResponse, FeedbackCreate, FeedbackResponse
from utils.dependencies import get_current_teacher

router = APIRouter(prefix="/api/analysis", tags=["analysis"])

# Another teacher's analysis is reported as not-found: scores, breakdown and
# the explanation are the most sensitive payload in the system.
_OWNERSHIP_ERRORS = (AnalysisNotFoundError, AnalysisForbiddenError)


@router.get("/{analysis_id}", response_model=AnalysisResultResponse)
async def get_analysis(
    analysis_id: int,
    db: Session = Depends(get_db),
    current_teacher: Teacher = Depends(get_current_teacher),
) -> AnalysisResultResponse:
    try:
        return AnalysisService(db).get_analysis(analysis_id, current_teacher.id)
    except _OWNERSHIP_ERRORS as exc:
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
    current_teacher: Teacher = Depends(get_current_teacher),
) -> FeedbackResponse:
    try:
        return AnalysisService(db).submit_feedback(
            analysis_id, current_teacher.id, body
        )
    except _OWNERSHIP_ERRORS as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc
