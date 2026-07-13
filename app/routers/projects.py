from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.auth import get_current_user, require_admin
from app.database import get_db
from app.models import Project
from app.schemas import ProjectCreate, ProjectRead


router = APIRouter(prefix="/projects", tags=["项目管理"], dependencies=[Depends(get_current_user)])


@router.post("", response_model=ProjectRead, summary="创建项目")
def create_project(payload: ProjectCreate, db: Session = Depends(get_db)):
    project = Project(name=payload.name, description=payload.description)
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


@router.get("", response_model=List[ProjectRead], summary="获取项目列表")
def list_projects(db: Session = Depends(get_db)):
    return db.query(Project).order_by(Project.id.desc()).all()


@router.get("/{project_id}", response_model=ProjectRead, summary="获取项目详情")
def get_project(project_id: int, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if project is None:
        raise HTTPException(status_code=404, detail="项目不存在")
    return project


@router.delete("/{project_id}", summary="删除项目")
def delete_project(
    project_id: int,
    db: Session = Depends(get_db),
    _admin=Depends(require_admin),
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if project is None:
        raise HTTPException(status_code=404, detail="项目不存在")
    db.delete(project)
    db.commit()
    return {"message": "项目已删除", "project_id": project_id}
