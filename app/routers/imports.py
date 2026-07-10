from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.schemas import ImportDocumentRequest, ImportResult
from app.services.importer import import_openapi, import_postman


router = APIRouter(prefix="/import", tags=["import"], dependencies=[Depends(get_current_user)])


@router.post("/openapi/{project_id}", response_model=ImportResult)
def import_openapi_document(project_id: int, payload: ImportDocumentRequest, db: Session = Depends(get_db)):
    try:
        imported, skipped, endpoint_ids = import_openapi(db, project_id, payload.content, payload.base_url)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return ImportResult(
        imported=imported,
        skipped=skipped,
        endpoint_ids=endpoint_ids,
        message=f"OpenAPI 导入完成：新增 {imported}，跳过 {skipped}",
    )


@router.post("/postman/{project_id}", response_model=ImportResult)
def import_postman_document(project_id: int, payload: ImportDocumentRequest, db: Session = Depends(get_db)):
    try:
        imported, skipped, endpoint_ids = import_postman(db, project_id, payload.content, payload.base_url)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return ImportResult(
        imported=imported,
        skipped=skipped,
        endpoint_ids=endpoint_ids,
        message=f"Postman 导入完成：新增 {imported}，跳过 {skipped}",
    )
