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
    tags=["测试用例"],
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
        assertions=from_json_text(case.assertions_json, []),
        extractors=from_json_text(case.extractors_json, []),
        reason=case.reason,
        created_by_ai=case.created_by_ai,
        created_at=case.created_at,
    )


def _apply_payload(case: TestCase, payload: TestCaseCreate) -> None:
    case.title = payload.title
    case.category = payload.category
    case.request_headers_json = to_json_text(payload.request_headers)
    case.request_body_json = to_json_text(payload.request_body)
    case.expected_status = payload.expected_status
    case.expected_contains = payload.expected_contains
    case.assertions_json = to_json_text(payload.assertions)
    case.extractors_json = to_json_text(payload.extractors)
    case.reason = payload.reason
    case.created_by_ai = payload.created_by_ai


@router.post("", response_model=TestCaseRead, summary="创建测试用例")
def create_case(endpoint_id: int, payload: TestCaseCreate, db: Session = Depends(get_db)):
    endpoint = db.query(ApiEndpoint).filter(ApiEndpoint.id == endpoint_id).first()
    if endpoint is None:
        raise HTTPException(status_code=404, detail="接口不存在")
    case = TestCase(
        endpoint_id=endpoint_id,
    )
    _apply_payload(case, payload)
    db.add(case)
    db.commit()
    db.refresh(case)
    return _case_to_read(case)


@router.get("", response_model=List[TestCaseRead], summary="获取测试用例列表")
def list_cases(endpoint_id: int, db: Session = Depends(get_db)):
    cases = db.query(TestCase).filter(TestCase.endpoint_id == endpoint_id).order_by(TestCase.id.desc()).all()
    return [_case_to_read(case) for case in cases]


@router.put("/{case_id}", response_model=TestCaseRead, summary="更新测试用例")
def update_case(endpoint_id: int, case_id: int, payload: TestCaseCreate, db: Session = Depends(get_db)):
    case = db.query(TestCase).filter(TestCase.endpoint_id == endpoint_id, TestCase.id == case_id).first()
    if case is None:
        raise HTTPException(status_code=404, detail="测试用例不存在")
    _apply_payload(case, payload)
    db.commit()
    db.refresh(case)
    return _case_to_read(case)


@router.post("/generate", response_model=List[TestCaseRead], summary="生成并保存测试用例")
def generate_and_save_cases(
    endpoint_id: int,
    payload: GenerateCasesRequest,
    db: Session = Depends(get_db),
):
    endpoint = db.query(ApiEndpoint).filter(ApiEndpoint.id == endpoint_id).first()
    if endpoint is None:
        raise HTTPException(status_code=404, detail="接口不存在")
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
            assertions_json=to_json_text([]),
            extractors_json=to_json_text([]),
            reason=draft["reason"],
            created_by_ai=provider == "openai",
        )
        db.add(case)
        created.append(case)
    db.commit()
    for case in created:
        db.refresh(case)
    return [_case_to_read(case) for case in created]


@router.delete("/{case_id}", summary="删除测试用例")
def delete_case(endpoint_id: int, case_id: int, db: Session = Depends(get_db)):
    case = db.query(TestCase).filter(TestCase.endpoint_id == endpoint_id, TestCase.id == case_id).first()
    if case is None:
        raise HTTPException(status_code=404, detail="测试用例不存在")
    db.delete(case)
    db.commit()
    return {"message": "测试用例已删除", "case_id": case_id}
