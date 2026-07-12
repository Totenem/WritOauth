from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database.connection import get_db
from schemas.subject import SubjectCreate, SubjectResponse, SubjectUpdate

router = APIRouter(prefix="/api/subjects", tags=["subjects"])


@router.get("", response_model=list[SubjectResponse])
async def list_subjects(db: Session = Depends(get_db)) -> list:
    return []


@router.post("", response_model=SubjectResponse, status_code=201)
async def create_subject(body: SubjectCreate, db: Session = Depends(get_db)) -> dict:
    return {"status": "not_implemented"}


@router.get("/{subject_id}", response_model=SubjectResponse)
async def get_subject(subject_id: int, db: Session = Depends(get_db)) -> dict:
    return {"status": "not_implemented"}


@router.put("/{subject_id}", response_model=SubjectResponse)
async def update_subject(
    subject_id: int, body: SubjectUpdate, db: Session = Depends(get_db)
) -> dict:
    return {"status": "not_implemented"}


@router.delete("/{subject_id}", status_code=204)
async def delete_subject(subject_id: int, db: Session = Depends(get_db)) -> None:
    return None
