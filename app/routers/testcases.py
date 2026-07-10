from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.auth import get_current_user
from app.config import OPENAI_MODEL
from app.database import get_db
from app.models import ApiEndpoint, TestCase
from app.schemas import GenerateCasesRequest, TestCaseCreate, TestCaseRead
from app.services.openai_case_generator import generate_cases_smart
from app.utils import from_json_text, to_json_text


router = APIRouter(
    prefix="/endpoints/{endpoint_id}/cases",
    tags=["test cases"],
    dependencies=[Depends(get_current_user)],
)


def _case_to_read(case: TestCase) -> TestCaseRead:
    return TestCaseRead(
        id=case.id,
        endpoint_id=case.endpoint_id,
        title=case.title,
        category=case.category,
        request_headers=from_json_text(case.request_headers_json),
        request_body=from_json_text(case.request_body_json),
        expected_status=case.expected_status,
        expected_contains=case.expected_contains,
        reason=case.reason,
        created_by_ai=case.created_by_ai,
        created_at=case.created_at,
    )


@router.post("", response_model=TestCaseRead)
def create_case(endpoint_id: int, payload: TestCaseCreate, db: Session = Depends(get_db)):
    endpoint = db.query(ApiEndpoint).filter(ApiEndpoint.id == endpoint_id).first()
    if endpoint is None:
        raise HTTPException(status_code=404, detail="endpoint not found")
    case = TestCase(
        endpoint_id=endpoint_id,
        title=payload.title,
        category=payload.category,
        request_headers_json=to_json_text(payload.request_headers),
        request_body_json=to_json_text(payload.request_body),
        expected_status=payload.expected_status,
        expected_contains=payload.expected_contains,
        reason=payload.reason,
        created_by_ai=payload.created_by_ai,
    )
    db.add(case)
    db.commit()
    db.refresh(case)
    return _case_to_read(case)


@router.get("", response_model=List[TestCaseRead])
def list_cases(endpoint_id: int, db: Session = Depends(get_db)):
    cases = db.query(TestCase).filter(TestCase.endpoint_id == endpoint_id).order_by(TestCase.id.desc()).all()
    return [_case_to_read(case) for case in cases]


@router.post("/generate", response_model=List[TestCaseRead])
def generate_and_save_cases(
    endpoint_id: int,
    payload: GenerateCasesRequest,
    db: Session = Depends(get_db),
):
    endpoint = db.query(ApiEndpoint).filter(ApiEndpoint.id == endpoint_id).first()
    if endpoint is None:
        raise HTTPException(status_code=404, detail="endpoint not found")
    drafts, provider, _message = generate_cases_smart(
        requirement=payload.requirement,
        method=endpoint.method,
        url=endpoint.url,
        headers=from_json_text(endpoint.headers_json),
        body=from_json_text(endpoint.body_json),
        expected_status=endpoint.expected_status,
        use_ai=payload.use_ai,
    )
    created: List[TestCase] = []
    for draft in drafts:
        case = TestCase(
            endpoint_id=endpoint.id,
            title=draft["title"],
            category=draft["category"],
            request_headers_json=to_json_text(draft["request_headers"]),
            request_body_json=to_json_text(draft["request_body"]),
            expected_status=draft["expected_status"],
            expected_contains=draft.get("expected_contains"),
            reason=draft["reason"],
            created_by_ai=provider == "openai",
        )
        db.add(case)
        created.append(case)
    db.commit()
    for case in created:
        db.refresh(case)
    return [_case_to_read(case) for case in created]


@router.delete("/{case_id}")
def delete_case(endpoint_id: int, case_id: int, db: Session = Depends(get_db)):
    case = db.query(TestCase).filter(TestCase.endpoint_id == endpoint_id, TestCase.id == case_id).first()
    if case is None:
        raise HTTPException(status_code=404, detail="case not found")
    db.delete(case)
    db.commit()
    return {"message": "case deleted", "case_id": case_id}
