from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from application.repositories.teacher_repository import TeacherEmailAlreadyExistsError
from application.services.auth_service import AuthService, InvalidCredentialsError
from database.connection import get_db
from models.teacher import Teacher
from schemas.auth import LoginRequest, TokenResponse
from schemas.teacher import TeacherCreate, TeacherResponse
from utils.dependencies import get_current_teacher

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post(
    "/register", response_model=TeacherResponse, status_code=status.HTTP_201_CREATED
)
async def register(
    data: TeacherCreate, db: Session = Depends(get_db)
) -> TeacherResponse:
    try:
        return AuthService(db).register(data)
    except TeacherEmailAlreadyExistsError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=str(exc)
        ) from exc


@router.post("/login", response_model=TokenResponse)
async def login(
    credentials: LoginRequest, db: Session = Depends(get_db)
) -> TokenResponse:
    try:
        return AuthService(db).login(credentials)
    except InvalidCredentialsError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)
        ) from exc


@router.get("/me", response_model=TeacherResponse)
async def me(current_teacher: Teacher = Depends(get_current_teacher)) -> Teacher:
    return current_teacher


@router.post("/logout")
async def logout() -> dict:
    # Stateless JWT: no server-side session to clear, so this is an intentional no-op.
    return {"status": "ok"}
