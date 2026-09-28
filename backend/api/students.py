from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from application.services.student_service import (
    StudentForbiddenError,
    StudentNotFoundError,
    StudentService,
    SubjectNotEnrollableError,
)
from database.connection import get_db
from models.teacher import Teacher
from schemas.student import StudentCreate, StudentResponse, StudentUpdate
from utils.dependencies import get_current_teacher

router = APIRouter(prefix="/api/students", tags=["students"])

# Cross-owner access is reported the same as not-found (404) so a teacher
# can't tell another teacher's student even exists. Matches api/subjects.py.
_OWNERSHIP_ERRORS = (StudentNotFoundError, StudentForbiddenError)


@router.get("", response_model=list[StudentResponse])
async def list_students(
    db: Session = Depends(get_db),
    current_teacher: Teacher = Depends(get_current_teacher),
) -> list[StudentResponse]:
    return StudentService(db).list_students(current_teacher.id)


@router.post("", response_model=StudentResponse, status_code=status.HTTP_201_CREATED)
async def create_student(
    body: StudentCreate,
    db: Session = Depends(get_db),
    current_teacher: Teacher = Depends(get_current_teacher),
) -> StudentResponse:
    try:
        return StudentService(db).create_student(current_teacher.id, body)
    except SubjectNotEnrollableError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc


@router.get("/{student_id}", response_model=StudentResponse)
async def get_student(
    student_id: int,
    db: Session = Depends(get_db),
    current_teacher: Teacher = Depends(get_current_teacher),
) -> StudentResponse:
    try:
        return StudentService(db).get_student(student_id, current_teacher.id)
    except _OWNERSHIP_ERRORS as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc


@router.put("/{student_id}", response_model=StudentResponse)
async def update_student(
    student_id: int,
    body: StudentUpdate,
    db: Session = Depends(get_db),
    current_teacher: Teacher = Depends(get_current_teacher),
) -> StudentResponse:
    try:
        return StudentService(db).update_student(student_id, current_teacher.id, body)
    except _OWNERSHIP_ERRORS as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc


@router.delete("/{student_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_student(
    student_id: int,
    db: Session = Depends(get_db),
    current_teacher: Teacher = Depends(get_current_teacher),
) -> None:
    try:
        StudentService(db).delete_student(student_id, current_teacher.id)
    except _OWNERSHIP_ERRORS as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc
