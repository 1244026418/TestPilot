from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.auth import get_current_user
from app.database import get_db
from app.models import ApiEndpoint, Project
from app.schemas import EndpointCreate, EndpointRead
from app.utils import from_json_text, to_json_text


router = APIRouter(
    prefix="/projects/{project_id}/endpoints",
    tags=["endpoints"],
    dependencies=[Depends(get_current_user)],
)


def _endpoint_to_read(endpoint: ApiEndpoint) -> EndpointRead:
    return EndpointRead(
        id=endpoint.id,
        project_id=endpoint.project_id,
        name=endpoint.name,
        method=endpoint.method,
        url=endpoint.url,
        headers=from_json_text(endpoint.headers_json),
        body=from_json_text(endpoint.body_json),
        expected_status=endpoint.expected_status,
        created_at=endpoint.created_at,
    )


@router.post("", response_model=EndpointRead)
def create_endpoint(project_id: int, payload: EndpointCreate, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if project is None:
        raise HTTPException(status_code=404, detail="project not found")
    endpoint = ApiEndpoint(
        project_id=project_id,
        name=payload.name,
        method=payload.method.upper(),
        url=payload.url,
        headers_json=to_json_text(payload.headers),
        body_json=to_json_text(payload.body),
        expected_status=payload.expected_status,
    )
    db.add(endpoint)
    db.commit()
    db.refresh(endpoint)
    return _endpoint_to_read(endpoint)


@router.get("", response_model=List[EndpointRead])
def list_endpoints(project_id: int, db: Session = Depends(get_db)):
    endpoints = db.query(ApiEndpoint).filter(ApiEndpoint.project_id == project_id).order_by(ApiEndpoint.id.desc()).all()
    return [_endpoint_to_read(endpoint) for endpoint in endpoints]


@router.delete("/{endpoint_id}")
def delete_endpoint(project_id: int, endpoint_id: int, db: Session = Depends(get_db)):
    endpoint = (
        db.query(ApiEndpoint)
        .filter(ApiEndpoint.project_id == project_id, ApiEndpoint.id == endpoint_id)
        .first()
    )
    if endpoint is None:
        raise HTTPException(status_code=404, detail="endpoint not found")
    db.delete(endpoint)
    db.commit()
    return {"message": "endpoint deleted", "endpoint_id": endpoint_id}
