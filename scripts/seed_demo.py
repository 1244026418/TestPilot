from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.database import SessionLocal, init_db
from app.models import ApiEndpoint, Project, TestCase, TestEnvironment
from app.utils import to_json_text


def upsert_endpoint(db, project_id, name, method, url, headers, body, expected_status):
    endpoint = (
        db.query(ApiEndpoint)
        .filter(ApiEndpoint.project_id == project_id, ApiEndpoint.name == name)
        .first()
    )
    if endpoint is None:
        endpoint = ApiEndpoint(project_id=project_id, name=name)
        db.add(endpoint)
    endpoint.method = method
    endpoint.url = url
    endpoint.headers_json = to_json_text(headers)
    endpoint.body_json = to_json_text(body)
    endpoint.expected_status = expected_status
    db.flush()
    return endpoint


def upsert_case(
    db,
    endpoint_id,
    title,
    category,
    body,
    expected_status,
    reason,
    *,
    headers=None,
    assertions=None,
    extractors=None,
):
    case = (
        db.query(TestCase)
        .filter(TestCase.endpoint_id == endpoint_id, TestCase.title == title)
        .first()
    )
    if case is None:
        case = TestCase(endpoint_id=endpoint_id, title=title)
        db.add(case)
    case.category = category
    case.request_headers_json = to_json_text(headers or {})
    case.request_body_json = to_json_text(body)
    case.expected_status = expected_status
    case.expected_contains = None
    case.assertions_json = to_json_text(assertions or [])
    case.extractors_json = to_json_text(extractors or [])
    case.reason = reason
    case.created_by_ai = False


def main() -> None:
    init_db()
    db = SessionLocal()
    try:
        project = db.query(Project).filter(Project.name == "Demo API 自动化测试").first()
        if project is None:
            project = Project(
                name="Demo API 自动化测试",
                description="演示环境切换、五类断言以及登录 Token 链式传递。",
            )
            db.add(project)
            db.flush()
        else:
            project.description = "演示环境切换、五类断言以及登录 Token 链式传递。"

        environment = (
            db.query(TestEnvironment)
            .filter(TestEnvironment.project_id == project.id, TestEnvironment.name == "本地演示环境")
            .first()
        )
        if environment is None:
            environment = TestEnvironment(project_id=project.id, name="本地演示环境")
            db.add(environment)
        environment.base_url = "http://127.0.0.1:8000"
        environment.variables_json = to_json_text({"demo_username": "demo"})
        environment.is_active = True
        db.flush()
        db.query(TestEnvironment).filter(
            TestEnvironment.project_id == project.id,
            TestEnvironment.id != environment.id,
        ).update({TestEnvironment.is_active: False}, synchronize_session=False)

        login_endpoint = upsert_endpoint(
            db,
            project.id,
            "用户登录",
            "POST",
            "/demo-target/login",
            {"Content-Type": "application/json"},
            {"username": "{{demo_username}}", "password": "123456"},
            200,
        )
        profile_endpoint = upsert_endpoint(
            db,
            project.id,
            "获取用户信息",
            "GET",
            "/demo-target/profile",
            {"Authorization": "Bearer {{token}}"},
            {},
            200,
        )
        order_endpoint = upsert_endpoint(
            db,
            project.id,
            "创建订单",
            "POST",
            "/demo-target/orders",
            {"Content-Type": "application/json"},
            {"product_id": 1, "quantity": 2},
            200,
        )

        db.query(TestCase).filter(
            TestCase.endpoint_id == login_endpoint.id,
            TestCase.title.in_(["登录成功", "密码错误"]),
        ).delete(synchronize_session=False)

        upsert_case(
            db,
            login_endpoint.id,
            "登录成功并提取 Token",
            "normal",
            {"username": "{{demo_username}}", "password": "123456"},
            200,
            "验证登录响应，并从 JSON 中提取 Token 供后续接口使用。",
            assertions=[
                {"type": "status", "operator": "eq", "expected": 200},
                {"type": "jsonpath", "target": "$.username", "operator": "eq", "expected": "demo"},
                {"type": "header", "target": "X-Demo-Service", "operator": "eq", "expected": "TestPilot"},
                {"type": "response_time", "operator": "lte", "expected": 2000},
                {
                    "type": "json_schema",
                    "schema": {
                        "type": "object",
                        "required": ["token", "username"],
                        "properties": {
                            "token": {"type": "string"},
                            "username": {"type": "string"},
                        },
                    },
                },
            ],
            extractors=[{"name": "token", "expression": "$.token"}],
        )
        upsert_case(
            db,
            profile_endpoint.id,
            "携带 Token 获取用户信息",
            "auth",
            {},
            200,
            "验证前置登录提取的 Token 能自动写入 Authorization 请求头。",
            headers={"Authorization": "Bearer {{token}}"},
            assertions=[
                {"type": "status", "operator": "eq", "expected": 200},
                {"type": "jsonpath", "target": "$.role", "operator": "eq", "expected": "tester"},
            ],
        )
        upsert_case(
            db,
            order_endpoint.id,
            "下单数量越界",
            "boundary",
            {"product_id": 1, "quantity": 0},
            400,
            "验证数量为零时触发参数边界校验。",
            assertions=[
                {"type": "status", "operator": "eq", "expected": 400},
                {"type": "jsonpath", "target": "$.detail", "operator": "contains", "expected": "range"},
            ],
        )
        db.commit()
        print(f"演示数据已就绪，project_id={project.id}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
