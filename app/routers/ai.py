from fastapi import APIRouter, Depends

from typing import List

from app.auth import get_current_user
from app.config import OPENAI_MODEL
from app.schemas import AIGenerateRequest, AIGenerateResponse
from app.services.openai_case_generator import generate_cases_smart


router = APIRouter(prefix="/ai", tags=["ai"], dependencies=[Depends(get_current_user)])


@router.post("/generate-cases", response_model=AIGenerateResponse)
def generate_case_drafts(payload: AIGenerateRequest):
    cases, provider, message = generate_cases_smart(
        requirement=payload.requirement,
        method=payload.method,
        url=payload.url,
        headers=payload.headers,
        body=payload.body,
        expected_status=payload.expected_status,
        use_ai=payload.use_ai,
    )
    return AIGenerateResponse(
        provider=provider,
        model=OPENAI_MODEL if provider == "openai" else None,
        message=message,
        cases=cases,
    )
