from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.database import SessionLocal, init_db
from app.models import ApiEndpoint, Project, TestCase
from app.utils import to_json_text


def get_or_create_endpoint(db, project_id, name, method, url, headers, body, expected_status):
    endpoint = (
        db.query(ApiEndpoint)
        .filter(ApiEndpoint.project_id == project_id, ApiEndpoint.name == name)
        .first()
    )
    if endpoint is not None:
        return endpoint
    endpoint = ApiEndpoint(
        project_id=project_id,
        name=name,
        method=method,
        url=url,
        headers_json=to_json_text(headers),
        body_json=to_json_text(body),
        expected_status=expected_status,
    )
    db.add(endpoint)
    db.commit()
    db.refresh(endpoint)
    return endpoint


def add_case_if_missing(db, endpoint_id, title, category, body, expected_status, reason, expected_contains=None):
    exists = (
        db.query(TestCase)
        .filter(TestCase.endpoint_id == endpoint_id, TestCase.title == title)
        .first()
    )
    if exists is not None:
        return
    db.add(
        TestCase(
            endpoint_id=endpoint_id,
            title=title,
            category=category,
            request_body_json=to_json_text(body),
            expected_status=expected_status,
            expected_contains=expected_contains,
            reason=reason,
            created_by_ai=False,
        )
    )


def main() -> None:
    init_db()
    db = SessionLocal()
    try:
        project = db.query(Project).filter(Project.name == "Demo API 自动化测试").first()
        if project is None:
            project = Project(name="Demo API 自动化测试", description="用于演示 TestPilot 的登录和下单接口测试。")
            db.add(project)
            db.commit()
            db.refresh(project)

        login_endpoint = get_or_create_endpoint(
            db=db,
            project_id=project.id,
            name="用户登录",
            method="POST",
            url="http://127.0.0.1:8000/demo-target/login",
            headers={"Content-Type": "application/json"},
            body={"username": "demo", "password": "123456"},
            expected_status=200,
        )
        order_endpoint = get_or_create_endpoint(
            db=db,
            project_id=project.id,
            name="创建订单",
            method="POST",
            url="http://127.0.0.1:8000/demo-target/orders",
            headers={"Content-Type": "application/json"},
            body={"product_id": 1, "quantity": 2},
            expected_status=200,
        )

        add_case_if_missing(
            db=db,
            endpoint_id=login_endpoint.id,
            title="登录成功",
            category="normal",
            body={"username": "demo", "password": "123456"},
            expected_status=200,
            expected_contains="demo-token",
            reason="验证正确账号密码可登录。",
        )
        add_case_if_missing(
            db=db,
            endpoint_id=login_endpoint.id,
            title="密码错误",
            category="auth",
            body={"username": "demo", "password": "wrong"},
            expected_status=401,
            reason="验证错误密码不可登录。",
        )
        add_case_if_missing(
            db=db,
            endpoint_id=order_endpoint.id,
            title="下单数量越界",
            category="boundary",
            body={"product_id": 1, "quantity": 0},
            expected_status=400,
            reason="验证数量边界校验。",
        )
        db.commit()
        print(f"Seeded project_id={project.id}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
