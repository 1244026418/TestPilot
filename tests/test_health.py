from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app


def test_health_and_frontend_fallback():
    with TestClient(app) as client:
        health = client.get("/api/health")
        home = client.get("/")
    assert health.status_code == 200
    assert health.json() == {"status": "ok"}
    assert home.status_code == 200
    assert home.json()["name"] == "TestPilot"


def test_auth_and_protected_dashboard():
    username = f"tester_{uuid4().hex[:8]}"
    with TestClient(app) as client:
        unauthorized = client.get("/api/dashboard/stats")
        registered = client.post("/api/auth/register", json={"username": username, "password": "123456"})
        token = registered.json()["access_token"]
        dashboard = client.get("/api/dashboard/stats", headers={"Authorization": f"Bearer {token}"})
        me = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert unauthorized.status_code == 401
    assert registered.status_code == 200
    assert registered.json()["user"]["role"] == "admin"
    assert dashboard.status_code == 200
    assert me.json()["username"] == username


def test_openapi_import():
    username = f"importer_{uuid4().hex[:8]}"
    document = {
        "openapi": "3.0.0",
        "servers": [{"url": "https://api.example.com"}],
        "paths": {
            "/users": {
                "post": {
                    "summary": "创建用户",
                    "requestBody": {"content": {"application/json": {"schema": {"type": "object", "properties": {"name": {"type": "string"}}}}}},
                    "responses": {"201": {"description": "created"}},
                }
            }
        },
    }
    import json

    with TestClient(app) as client:
        auth = client.post("/api/auth/register", json={"username": username, "password": "123456"}).json()
        headers = {"Authorization": f"Bearer {auth['access_token']}"}
        project = client.post("/api/projects", json={"name": "导入测试", "description": ""}, headers=headers).json()
        result = client.post(
            f"/api/import/openapi/{project['id']}",
            json={"content": json.dumps(document), "base_url": ""},
            headers=headers,
        )
        endpoints = client.get(f"/api/projects/{project['id']}/endpoints", headers=headers)
    assert result.status_code == 200
    assert result.json()["imported"] == 1
    assert endpoints.json()[0]["expected_status"] == 201
