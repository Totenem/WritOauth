from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from application.services.paper_service import (
    PaperInvalidReferenceError,
    PaperNotFoundError,
    PaperService,
)
from database.connection import get_db
from models.teacher import Teacher
from schemas.paper import AnalysisPaperCreate, BaselinePaperCreate, PaperResponse
from utils.dependencies import get_current_teacher

router = APIRouter(prefix="/api/papers", tags=["papers"])


@router.post(
    "/baseline", response_model=PaperResponse, status_code=status.HTTP_201_CREATED
)
async def upload_baseline(
    body: BaselinePaperCreate,
    db: Session = Depends(get_db),
    _current_teacher: Teacher = Depends(get_current_teacher),
) -> PaperResponse:
    try:
        return PaperService(db).upload_baseline(body)
    except PaperInvalidReferenceError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
        ) from exc


@router.post(
    "/analyze", response_model=PaperResponse, status_code=status.HTTP_201_CREATED
)
async def upload_for_analysis(
    body: AnalysisPaperCreate,
    db: Session = Depends(get_db),
    _current_teacher: Teacher = Depends(get_current_teacher),
) -> PaperResponse:
    try:
        return PaperService(db).upload_for_analysis(body)
    except PaperInvalidReferenceError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
        ) from exc


@router.get("/{paper_id}", response_model=PaperResponse)
async def get_paper(
    paper_id: int,
    db: Session = Depends(get_db),
    _current_teacher: Teacher = Depends(get_current_teacher),
) -> PaperResponse:
    try:
        return PaperService(db).get_paper(paper_id)
    except PaperNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc
