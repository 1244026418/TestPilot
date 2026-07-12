from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app


def test_case_can_be_created_and_updated_with_assertions():
    with TestClient(app) as client:
        username = f"case_{uuid4().hex[:8]}"
        auth = client.post("/api/auth/register", json={"username": username, "password": "123456"}).json()
        headers = {"Authorization": f"Bearer {auth['access_token']}"}
        project = client.post("/api/projects", json={"name": "用例编辑测试"}, headers=headers).json()
        endpoint = client.post(
            f"/api/projects/{project['id']}/endpoints",
            json={"name": "用户信息", "method": "GET", "url": "/profile"},
            headers=headers,
        ).json()
        created = client.post(
            f"/api/endpoints/{endpoint['id']}/cases",
            json={"title": "初始用例", "assertions": [{"type": "status", "expected": 200}]},
            headers=headers,
        ).json()
        updated = client.put(
            f"/api/endpoints/{endpoint['id']}/cases/{created['id']}",
            json={
                "title": "鉴权用例",
                "category": "auth",
                "request_headers": {"Authorization": "Bearer {{token}}"},
                "assertions": [{"type": "jsonpath", "target": "$.role", "operator": "eq", "expected": "tester"}],
                "extractors": [{"name": "user_id", "expression": "$.id"}],
            },
            headers=headers,
        )

    assert updated.status_code == 200
    assert updated.json()["title"] == "鉴权用例"
    assert updated.json()["request_headers"]["Authorization"] == "Bearer {{token}}"
    assert updated.json()["assertions"][0]["target"] == "$.role"
    assert updated.json()["extractors"] == [{"name": "user_id", "expression": "$.id"}]
