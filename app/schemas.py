from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=64)
    password: str = Field(min_length=6, max_length=128)


class UserLogin(BaseModel):
    username: str
    password: str


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    role: str
    created_at: datetime


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserRead


class ProjectCreate(BaseModel):
    name: str = Field(min_length=1, max_length=128)
    description: str = ""


class ProjectRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str
    created_at: datetime


class EndpointCreate(BaseModel):
    name: str = Field(min_length=1, max_length=128)
    method: str = "GET"
    url: str
    headers: Dict[str, Any] = Field(default_factory=dict)
    body: Dict[str, Any] = Field(default_factory=dict)
    expected_status: int = 200


class EndpointRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int
    name: str
    method: str
    url: str
    headers: Dict[str, Any]
    body: Dict[str, Any]
    expected_status: int
    created_at: datetime


class TestCaseCreate(BaseModel):
    title: str = Field(min_length=1, max_length=160)
    category: str = "normal"
    request_headers: Dict[str, Any] = Field(default_factory=dict)
    request_body: Dict[str, Any] = Field(default_factory=dict)
    expected_status: Optional[int] = None
    expected_contains: Optional[str] = None
    reason: str = ""
    created_by_ai: bool = False


class TestCaseRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    endpoint_id: int
    title: str
    category: str
    request_headers: Dict[str, Any]
    request_body: Dict[str, Any]
    expected_status: Optional[int]
    expected_contains: Optional[str]
    reason: str
    created_by_ai: bool
    created_at: datetime


class GenerateCasesRequest(BaseModel):
    requirement: str = Field(min_length=4)
    use_ai: bool = True


class AIGenerateRequest(BaseModel):
    requirement: str = Field(min_length=4)
    method: str = "GET"
    url: str = "http://127.0.0.1:8000/demo-target/login"
    headers: Dict[str, Any] = Field(default_factory=dict)
    body: Dict[str, Any] = Field(default_factory=dict)
    expected_status: int = 200
    use_ai: bool = True


class GeneratedCase(BaseModel):
    title: str
    category: str
    request_headers: Dict[str, Any]
    request_body: Dict[str, Any]
    expected_status: int
    expected_contains: Optional[str] = None
    reason: str


class AIGenerateResponse(BaseModel):
    provider: str
    model: Optional[str] = None
    message: str = ""
    cases: List[GeneratedCase]


class TestResultRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    testcase_id: int
    status: str
    status_code: Optional[int]
    elapsed_ms: Optional[int]
    error: Optional[str]
    response_snippet: Optional[str]


class TestRunRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int
    status: str
    total: int
    passed: int
    failed: int
    report_path: Optional[str]
    started_at: datetime
    finished_at: Optional[datetime]
    results: List[TestResultRead] = Field(default_factory=list)


class DashboardStats(BaseModel):
    projects: int
    endpoints: int
    cases: int
    runs: int
    passed_runs: int
    failed_runs: int
    latest_run: Optional[TestRunRead] = None


class ImportDocumentRequest(BaseModel):
    content: str = Field(min_length=2)
    base_url: str = ""


class ImportResult(BaseModel):
    imported: int
    skipped: int
    endpoint_ids: List[int]
    message: str
