from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from application.services.subject_service import (
    SubjectForbiddenError,
    SubjectNotFoundError,
    SubjectService,
)
from database.connection import get_db
from models.teacher import Teacher
from schemas.subject import SubjectCreate, SubjectResponse, SubjectUpdate
from utils.dependencies import get_current_teacher

router = APIRouter(prefix="/api/subjects", tags=["subjects"])


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
