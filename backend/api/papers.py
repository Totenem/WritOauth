from typing import Literal

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy.orm import Session

from application.services.paper_service import (
    PaperForbiddenError,
    PaperInvalidReferenceError,
    PaperNotFoundError,
    PaperService,
)
from config.settings import get_settings
from database.connection import get_db
from models.teacher import Teacher
from schemas.paper import (
    AnalysisPaperCreate,
    BaselinePaperCreate,
    ExtractionResponse,
    PaperResponse,
)
from utils.dependencies import get_current_teacher
from utils.file_extraction import ExtractionError, extract_text

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


@router.get("", response_model=list[PaperResponse])
async def list_papers(
    student_id: int | None = None,
    subject_id: int | None = None,
    type: Literal["baseline", "submission"] | None = None,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    current_teacher: Teacher = Depends(get_current_teacher),
) -> list[PaperResponse]:
    """The caller's own papers, newest first.

    Filters narrow within the caller's scope and can never widen it: a
    student_id belonging to another teacher simply returns nothing.
    """
    return PaperService(db).list_papers(
        current_teacher.id,
        student_id=student_id,
        subject_id=subject_id,
        paper_type=type,
        limit=limit,
        offset=offset,
    )


@router.post("/extract", response_model=ExtractionResponse)
async def extract_document(
    file: UploadFile = File(...),
    _current_teacher: Teacher = Depends(get_current_teacher),
) -> ExtractionResponse:
    """Pull plain text out of an uploaded PDF, Word or text file.

    Deliberately separate from the upload endpoints rather than a multipart
    variant of them. The teacher reviews (and can correct) the extracted
    text before submitting it through `/baseline` or `/analyze`, so a bad
    extraction never silently becomes a student's baseline profile. It also
    leaves those endpoints and their contracts untouched.

    Nothing is persisted here - the file is parsed in memory and discarded.
    """
    data = await file.read()
    try:
        result = extract_text(
            file.filename or "", data, get_settings().max_upload_bytes
        )
    except ExtractionError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
        ) from exc

    return ExtractionResponse(
        filename=result.filename,
        source_format=result.source_format,
        text=result.text,
        word_count=result.word_count,
        page_count=result.page_count,
        warnings=result.warnings,
    )


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
