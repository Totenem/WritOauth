from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from application.services.dashboard_service import DashboardService
from database.connection import get_db
from models.teacher import Teacher
from schemas.dashboard import DashboardStats
from utils.dependencies import get_current_teacher

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/stats", response_model=DashboardStats)
async def dashboard_stats(
    db: Session = Depends(get_db),
    current_teacher: Teacher = Depends(get_current_teacher),
) -> DashboardStats:
    """Everything the dashboard needs, scoped to the signed-in teacher.

    A brand-new teacher gets a valid all-zero payload rather than an error -
    this is the page they land on straight after signing up, so the empty
    case is the first thing a real user sees.
    """
    return DashboardService(db).stats(current_teacher.id)
