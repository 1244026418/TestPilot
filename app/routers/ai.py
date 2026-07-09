from fastapi import APIRouter

from typing import List

from app.schemas import AIGenerateRequest, GeneratedCase
from app.services.ai_case_generator import generate_cases


router = APIRouter(prefix="/ai", tags=["ai"])


@router.post("/generate-cases", response_model=List[GeneratedCase])
def generate_case_drafts(payload: AIGenerateRequest):
    return generate_cases(
        requirement=payload.requirement,
        method=payload.method,
        url=payload.url,
        headers=payload.headers,
        body=payload.body,
        expected_status=payload.expected_status,
    )
