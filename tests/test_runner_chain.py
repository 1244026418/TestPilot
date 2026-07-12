import json

from app.database import SessionLocal, init_db
from app.models import ApiEndpoint, Project, TestCase as CaseModel, TestEnvironment as EnvironmentModel
from app.services.runner import execute_project
from app.utils import to_json_text


class FakeResponse:
    def __init__(self, status_code, payload, headers=None):
        self.status_code = status_code
        self._payload = payload
        self.text = json.dumps(payload)
        self.headers = headers or {"Content-Type": "application/json"}

    def json(self):
        return self._payload


def test_runner_extracts_token_and_uses_it_in_later_request(monkeypatch):
    init_db()
    db = SessionLocal()
    calls = []

    def fake_request(**kwargs):
        calls.append(kwargs)
        if kwargs["url"].endswith("/login"):
            return FakeResponse(200, {"token": "runtime-secret", "username": "demo"})
        assert kwargs["headers"]["Authorization"] == "Bearer runtime-secret"
        return FakeResponse(200, {"username": "demo", "role": "tester"})

    monkeypatch.setattr("app.services.runner.requests.request", fake_request)
    try:
        project = Project(name="链式执行测试", description="")
        db.add(project)
        db.flush()
        environment = EnvironmentModel(
            project_id=project.id,
            name="测试环境",
            base_url="http://api.example.com",
            variables_json=to_json_text({"username": "demo"}),
            is_active=True,
        )
        login = ApiEndpoint(
            project_id=project.id,
            name="登录",
            method="POST",
            url="/login",
            headers_json="{}",
            body_json=to_json_text({"username": "{{username}}"}),
            expected_status=200,
        )
        profile = ApiEndpoint(
            project_id=project.id,
            name="个人信息",
            method="GET",
            url="/profile",
            headers_json=to_json_text({"Authorization": "Bearer {{token}}"}),
            body_json="{}",
            expected_status=200,
        )
        db.add_all([environment, login, profile])
        db.flush()
        db.add_all(
            [
                CaseModel(
                    endpoint_id=login.id,
                    title="提取 Token",
                    request_body_json=to_json_text({"username": "{{username}}"}),
                    assertions_json=to_json_text([{"type": "status", "expected": 200}]),
                    extractors_json=to_json_text([{"name": "token", "expression": "$.token"}]),
                ),
                CaseModel(
                    endpoint_id=profile.id,
                    title="使用 Token",
                    request_headers_json=to_json_text({"Authorization": "Bearer {{token}}"}),
                    assertions_json=to_json_text(
                        [{"type": "jsonpath", "target": "$.role", "operator": "eq", "expected": "tester"}]
                    ),
                ),
            ]
        )
        db.commit()

        run = execute_project(db, project.id, environment.id)

        assert run.status == "passed"
        assert run.total == 2
        assert calls[0]["url"] == "http://api.example.com/login"
        assert calls[1]["headers"]["Authorization"] == "Bearer runtime-secret"
        assert "runtime-secret" not in run.summary_json
        assert run.results[0].extracted_variables == ["token"]
        assert "runtime-secret" not in run.results[0].response_snippet
        assert "***" in run.results[0].response_snippet
    finally:
        db.close()


def test_runner_rejects_environment_from_another_project():
    init_db()
    db = SessionLocal()
    try:
        first = Project(name="项目 A", description="")
        second = Project(name="项目 B", description="")
        db.add_all([first, second])
        db.flush()
        environment = EnvironmentModel(project_id=second.id, name="B 环境", is_active=True)
        db.add(environment)
        db.commit()

        try:
            execute_project(db, first.id, environment.id)
            raised = False
        except ValueError as exc:
            raised = str(exc) == "environment not found"
        assert raised is True
    finally:
        db.close()
