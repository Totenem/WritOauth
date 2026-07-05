from fastapi import APIRouter

from schemas.auth import LoginRequest, TokenResponse

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
async def login(credentials: LoginRequest) -> dict:
    return {"access_token": "not_implemented", "token_type": "bearer"}


@router.post("/logout")
async def logout() -> dict:
    return {"status": "not_implemented"}
