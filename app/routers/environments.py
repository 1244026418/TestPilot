from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.models import Project, TestEnvironment, TestRun
from app.schemas import EnvironmentCreate, EnvironmentRead, EnvironmentUpdate
from app.utils import from_json_text, to_json_text


router = APIRouter(
    prefix="/projects/{project_id}/environments",
    tags=["环境管理"],
    dependencies=[Depends(get_current_user)],
)


def _environment_to_read(environment: TestEnvironment) -> EnvironmentRead:
    return EnvironmentRead(
        id=environment.id,
        project_id=environment.project_id,
        name=environment.name,
        base_url=environment.base_url,
        variables=from_json_text(environment.variables_json),
        is_active=environment.is_active,
        created_at=environment.created_at,
    )


def _activate(db: Session, project_id: int, environment_id: int) -> None:
    db.query(TestEnvironment).filter(TestEnvironment.project_id == project_id).update(
        {TestEnvironment.is_active: False},
        synchronize_session=False,
    )
    db.query(TestEnvironment).filter(TestEnvironment.id == environment_id).update(
        {TestEnvironment.is_active: True},
        synchronize_session=False,
    )


@router.post("", response_model=EnvironmentRead, summary="创建测试环境")
def create_environment(project_id: int, payload: EnvironmentCreate, db: Session = Depends(get_db)):
    if db.query(Project).filter(Project.id == project_id).first() is None:
        raise HTTPException(status_code=404, detail="项目不存在")
    has_environment = db.query(TestEnvironment.id).filter(TestEnvironment.project_id == project_id).first()
    environment = TestEnvironment(
        project_id=project_id,
        name=payload.name,
        base_url=payload.base_url.rstrip("/"),
        variables_json=to_json_text(payload.variables),
        is_active=payload.is_active or has_environment is None,
    )
    db.add(environment)
    db.flush()
    if environment.is_active:
        _activate(db, project_id, environment.id)
    db.commit()
    db.refresh(environment)
    return _environment_to_read(environment)


@router.get("", response_model=List[EnvironmentRead], summary="获取测试环境列表")
def list_environments(project_id: int, db: Session = Depends(get_db)):
    environments = (
        db.query(TestEnvironment)
        .filter(TestEnvironment.project_id == project_id)
        .order_by(TestEnvironment.is_active.desc(), TestEnvironment.id.asc())
        .all()
    )
    return [_environment_to_read(environment) for environment in environments]


@router.put("/{environment_id}", response_model=EnvironmentRead, summary="更新测试环境")
def update_environment(
    project_id: int,
    environment_id: int,
    payload: EnvironmentUpdate,
    db: Session = Depends(get_db),
):
    environment = (
        db.query(TestEnvironment)
        .filter(TestEnvironment.project_id == project_id, TestEnvironment.id == environment_id)
        .first()
    )
    if environment is None:
        raise HTTPException(status_code=404, detail="测试环境不存在")
    changes = payload.model_dump(exclude_unset=True)
    if "name" in changes:
        environment.name = changes["name"]
    if "base_url" in changes:
        environment.base_url = changes["base_url"].rstrip("/")
    if "variables" in changes:
        environment.variables_json = to_json_text(changes["variables"])
    if changes.get("is_active"):
        _activate(db, project_id, environment_id)
    db.commit()
    db.refresh(environment)
    return _environment_to_read(environment)


@router.delete("/{environment_id}", summary="删除测试环境")
def delete_environment(project_id: int, environment_id: int, db: Session = Depends(get_db)):
    environment = (
        db.query(TestEnvironment)
        .filter(TestEnvironment.project_id == project_id, TestEnvironment.id == environment_id)
        .first()
    )
    if environment is None:
        raise HTTPException(status_code=404, detail="测试环境不存在")
    was_active = environment.is_active
    db.query(TestRun).filter(TestRun.environment_id == environment_id).update(
        {TestRun.environment_id: None},
        synchronize_session=False,
    )
    db.delete(environment)
    db.flush()
    if was_active:
        replacement = (
            db.query(TestEnvironment)
            .filter(TestEnvironment.project_id == project_id)
            .order_by(TestEnvironment.id.asc())
            .first()
        )
        if replacement is not None:
            replacement.is_active = True
    db.commit()
    return {"message": "测试环境已删除", "environment_id": environment_id}
