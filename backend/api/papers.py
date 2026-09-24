from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from application.services.paper_service import (
    PaperForbiddenError,
    PaperInvalidReferenceError,
    PaperNotFoundError,
    PaperService,
)
from database.connection import get_db
from models.teacher import Teacher
from schemas.paper import AnalysisPaperCreate, BaselinePaperCreate, PaperResponse
from utils.dependencies import get_current_teacher

router = APIRouter(prefix="/api/papers", tags=["papers"])

# Not-found and not-yours are both 404 so a teacher can't probe which
# student/subject/paper ids exist outside their own roster.
_OWNERSHIP_ERRORS = (PaperNotFoundError, PaperForbiddenError)


@router.post(
    "/baseline", response_model=PaperResponse, status_code=status.HTTP_201_CREATED
)
async def upload_baseline(
    body: BaselinePaperCreate,
    db: Session = Depends(get_db),
    current_teacher: Teacher = Depends(get_current_teacher),
) -> PaperResponse:
    try:
        return PaperService(db).upload_baseline(body, current_teacher.id)
    except _OWNERSHIP_ERRORS as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc
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
    current_teacher: Teacher = Depends(get_current_teacher),
) -> PaperResponse:
    try:
        return PaperService(db).upload_for_analysis(body, current_teacher.id)
    except _OWNERSHIP_ERRORS as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc
    except PaperInvalidReferenceError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
        ) from exc


@router.get("/{paper_id}", response_model=PaperResponse)
async def get_paper(
    paper_id: int,
    db: Session = Depends(get_db),
    current_teacher: Teacher = Depends(get_current_teacher),
) -> PaperResponse:
    try:
        return PaperService(db).get_paper(paper_id, current_teacher.id)
    except _OWNERSHIP_ERRORS as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc
