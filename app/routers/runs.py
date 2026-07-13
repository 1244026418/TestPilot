from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from pathlib import Path
from sqlalchemy.orm import Session, selectinload
from typing import List, Optional

from app.auth import get_current_user
from app.database import get_db
from app.models import TestRun
from app.schemas import RunCreate, TestRunRead
from app.services.runner import execute_project


router = APIRouter(
    prefix="/projects/{project_id}/runs",
    tags=["测试执行"],
    dependencies=[Depends(get_current_user)],
)


@router.post("", response_model=TestRunRead, summary="执行项目测试")
def run_project(project_id: int, payload: Optional[RunCreate] = None, db: Session = Depends(get_db)):
    try:
        run = execute_project(db, project_id, payload.environment_id if payload else None)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    run = db.query(TestRun).options(selectinload(TestRun.results)).filter(TestRun.id == run.id).first()
    return run


@router.get("", response_model=List[TestRunRead], summary="获取执行记录")
def list_runs(project_id: int, db: Session = Depends(get_db)):
    return (
        db.query(TestRun)
        .options(selectinload(TestRun.results))
        .filter(TestRun.project_id == project_id)
        .order_by(TestRun.id.desc())
        .all()
    )


@router.get("/{run_id}/report", summary="下载 HTML 测试报告")
def get_run_report(project_id: int, run_id: int, db: Session = Depends(get_db)):
    run = db.query(TestRun).filter(TestRun.project_id == project_id, TestRun.id == run_id).first()
    if run is None:
        raise HTTPException(status_code=404, detail="执行记录不存在")
    if not run.report_path or not Path(run.report_path).exists():
        raise HTTPException(status_code=404, detail="测试报告不存在")
    return FileResponse(run.report_path, media_type="text/html", filename=f"run_{run.id}.html")
