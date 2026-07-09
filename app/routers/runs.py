from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from pathlib import Path
from sqlalchemy.orm import Session, selectinload
from typing import List

from app.database import get_db
from app.models import TestRun
from app.schemas import TestRunRead
from app.services.runner import execute_project


router = APIRouter(prefix="/projects/{project_id}/runs", tags=["runs"])


@router.post("", response_model=TestRunRead)
def run_project(project_id: int, db: Session = Depends(get_db)):
    try:
        run = execute_project(db, project_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    run = db.query(TestRun).options(selectinload(TestRun.results)).filter(TestRun.id == run.id).first()
    return run


@router.get("", response_model=List[TestRunRead])
def list_runs(project_id: int, db: Session = Depends(get_db)):
    return (
        db.query(TestRun)
        .options(selectinload(TestRun.results))
        .filter(TestRun.project_id == project_id)
        .order_by(TestRun.id.desc())
        .all()
    )


@router.get("/{run_id}/report")
def get_run_report(project_id: int, run_id: int, db: Session = Depends(get_db)):
    run = db.query(TestRun).filter(TestRun.project_id == project_id, TestRun.id == run_id).first()
    if run is None:
        raise HTTPException(status_code=404, detail="run not found")
    if not run.report_path or not Path(run.report_path).exists():
        raise HTTPException(status_code=404, detail="report not found")
    return FileResponse(run.report_path, media_type="text/html", filename=f"run_{run.id}.html")
