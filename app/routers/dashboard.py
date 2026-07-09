from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session, selectinload

from app.database import get_db
from app.models import ApiEndpoint, Project, TestCase, TestRun
from app.schemas import DashboardStats


router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/stats", response_model=DashboardStats)
def dashboard_stats(db: Session = Depends(get_db)):
    latest_run = (
        db.query(TestRun)
        .options(selectinload(TestRun.results))
        .order_by(TestRun.id.desc())
        .first()
    )
    return DashboardStats(
        projects=db.query(Project).count(),
        endpoints=db.query(ApiEndpoint).count(),
        cases=db.query(TestCase).count(),
        runs=db.query(TestRun).count(),
        passed_runs=db.query(TestRun).filter(TestRun.status == "passed").count(),
        failed_runs=db.query(TestRun).filter(TestRun.status == "failed").count(),
        latest_run=latest_run,
    )
