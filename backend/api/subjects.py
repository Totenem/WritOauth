from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from application.services.subject_service import (
    BatchUploadFormatError,
    SubjectForbiddenError,
    SubjectNotFoundError,
    SubjectService,
)
from config.settings import get_settings
from database.connection import get_db
from models.teacher import Teacher
from schemas.subject import (
    BatchUploadResult,
    RosterResponse,
    SubjectCreate,
    SubjectResponse,
    SubjectUpdate,
)
from utils.dependencies import get_current_teacher

router = APIRouter(prefix="/api/subjects", tags=["subjects"])

_OWNERSHIP_ERRORS = (SubjectNotFoundError, SubjectForbiddenError)


@router.get("", response_model=list[SubjectResponse])
async def list_subjects(
    db: Session = Depends(get_db),
    current_teacher: Teacher = Depends(get_current_teacher),
) -> list[SubjectResponse]:
    return SubjectService(db).list_subjects(current_teacher.id)


@router.post("", response_model=SubjectResponse, status_code=status.HTTP_201_CREATED)
async def create_subject(
    body: SubjectCreate,
    db: Session = Depends(get_db),
    current_teacher: Teacher = Depends(get_current_teacher),
) -> SubjectResponse:
    return SubjectService(db).create_subject(current_teacher.id, body)


@router.get("/{subject_id}", response_model=SubjectResponse)
async def get_subject(
    subject_id: int,
    db: Session = Depends(get_db),
    current_teacher: Teacher = Depends(get_current_teacher),
) -> SubjectResponse:
    try:
        return SubjectService(db).get_subject(subject_id, current_teacher.id)
    except (SubjectNotFoundError, SubjectForbiddenError) as exc:
        # Cross-owner access is reported the same as not-found (404) so a
        # teacher can't tell another teacher's subject even exists.
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc


@router.put("/{subject_id}", response_model=SubjectResponse)
async def update_subject(
    subject_id: int,
    body: SubjectUpdate,
    db: Session = Depends(get_db),
    current_teacher: Teacher = Depends(get_current_teacher),
) -> SubjectResponse:
    try:
        return SubjectService(db).update_subject(subject_id, current_teacher.id, body)
    except (SubjectNotFoundError, SubjectForbiddenError) as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc


@router.delete("/{subject_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_subject(
    subject_id: int,
    db: Session = Depends(get_db),
    current_teacher: Teacher = Depends(get_current_teacher),
) -> None:
    try:
        SubjectService(db).delete_subject(subject_id, current_teacher.id)
    except (SubjectNotFoundError, SubjectForbiddenError) as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc


@router.get("/{subject_id}/roster", response_model=RosterResponse)
async def get_roster(
    subject_id: int,
    db: Session = Depends(get_db),
    current_teacher: Teacher = Depends(get_current_teacher),
) -> RosterResponse:
    try:
        return SubjectService(db).get_roster(subject_id, current_teacher.id)
    except _OWNERSHIP_ERRORS as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc


@router.post("/{subject_id}/students/batch", response_model=BatchUploadResult)
async def batch_upload_students(
    subject_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_teacher: Teacher = Depends(get_current_teacher),
) -> BatchUploadResult:
    """Enroll many students into one course from the downloadable CSV template.

    Bad rows are skipped and reported individually; only a file that can't
    be read at all (wrong encoding, missing header) fails the whole request.
    """
    if not (file.filename or "").lower().endswith(".csv"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Upload a .csv file"
        )
    data = await file.read()
    if len(data) > get_settings().max_upload_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="File is too large"
        )
    try:
        return SubjectService(db).batch_upload(subject_id, current_teacher.id, data)
    except _OWNERSHIP_ERRORS as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc
    except BatchUploadFormatError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
        ) from exc
