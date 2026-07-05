from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database.connection import get_db
from schemas.student import StudentCreate, StudentUpdate, StudentResponse

router = APIRouter(prefix="/api/students", tags=["students"])


@router.get("", response_model=list[StudentResponse])
async def list_students(db: Session = Depends(get_db)) -> list:
    return []


@router.post("", response_model=StudentResponse, status_code=201)
async def create_student(body: StudentCreate, db: Session = Depends(get_db)) -> dict:
    return {"status": "not_implemented"}


@router.get("/{student_id}", response_model=StudentResponse)
async def get_student(student_id: int, db: Session = Depends(get_db)) -> dict:
    return {"status": "not_implemented"}


@router.put("/{student_id}", response_model=StudentResponse)
async def update_student(
    student_id: int, body: StudentUpdate, db: Session = Depends(get_db)
) -> dict:
    return {"status": "not_implemented"}


@router.delete("/{student_id}", status_code=204)
async def delete_student(student_id: int, db: Session = Depends(get_db)) -> None:
    return None
