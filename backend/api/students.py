from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from application.services.student_service import StudentNotFoundError, StudentService
from database.connection import get_db
from models.teacher import Teacher
from schemas.student import StudentCreate, StudentResponse, StudentUpdate
from utils.dependencies import get_current_teacher

router = APIRouter(prefix="/api/students", tags=["students"])


@router.get("", response_model=list[StudentResponse])
async def list_students(
    db: Session = Depends(get_db),
    _current_teacher: Teacher = Depends(get_current_teacher),
) -> list[StudentResponse]:
    return StudentService(db).list_students()


@router.post("", response_model=StudentResponse, status_code=status.HTTP_201_CREATED)
async def create_student(
    body: StudentCreate,
    db: Session = Depends(get_db),
    _current_teacher: Teacher = Depends(get_current_teacher),
) -> StudentResponse:
    return StudentService(db).create_student(body)


@router.get("/{student_id}", response_model=StudentResponse)
async def get_student(
    student_id: int,
    db: Session = Depends(get_db),
    _current_teacher: Teacher = Depends(get_current_teacher),
) -> StudentResponse:
    try:
        return StudentService(db).get_student(student_id)
    except StudentNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc


@router.put("/{student_id}", response_model=StudentResponse)
async def update_student(
    student_id: int,
    body: StudentUpdate,
    db: Session = Depends(get_db),
    _current_teacher: Teacher = Depends(get_current_teacher),
) -> StudentResponse:
    try:
        return StudentService(db).update_student(student_id, body)
    except StudentNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc


@router.delete("/{student_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_student(
    student_id: int,
    db: Session = Depends(get_db),
    _current_teacher: Teacher = Depends(get_current_teacher),
) -> None:
    try:
        StudentService(db).delete_student(student_id)
    except StudentNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc
