from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app


def auth_headers(client):
    username = f"env_{uuid4().hex[:8]}"
    response = client.post("/api/auth/register", json={"username": username, "password": "123456"})
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def test_environment_crud_and_single_active_rule():
    with TestClient(app) as client:
        headers = auth_headers(client)
        project = client.post("/api/projects", json={"name": "环境管理测试"}, headers=headers).json()
        first = client.post(
            f"/api/projects/{project['id']}/environments",
            json={"name": "开发环境", "base_url": "http://dev.example.com/", "variables": {"tenant": "dev"}},
            headers=headers,
        )
        second = client.post(
            f"/api/projects/{project['id']}/environments",
            json={"name": "测试环境", "base_url": "http://test.example.com", "variables": {}, "is_active": True},
            headers=headers,
        )
        environments = client.get(f"/api/projects/{project['id']}/environments", headers=headers).json()

        assert first.status_code == 200
        assert first.json()["base_url"] == "http://dev.example.com"
        assert second.status_code == 200
        assert sum(item["is_active"] for item in environments) == 1
        assert environments[0]["name"] == "测试环境"


def test_environment_update_and_delete_activates_replacement():
    with TestClient(app) as client:
        headers = auth_headers(client)
        project = client.post("/api/projects", json={"name": "环境切换测试"}, headers=headers).json()
        first = client.post(
            f"/api/projects/{project['id']}/environments",
            json={"name": "开发环境", "variables": {"version": 1}},
            headers=headers,
        ).json()
        second = client.post(
            f"/api/projects/{project['id']}/environments",
            json={"name": "测试环境", "is_active": True},
            headers=headers,
        ).json()
        updated = client.put(
            f"/api/projects/{project['id']}/environments/{first['id']}",
            json={"name": "开发环境-新版", "variables": {"version": 2}, "is_active": True},
            headers=headers,
        )
        deleted = client.delete(
            f"/api/projects/{project['id']}/environments/{first['id']}",
            headers=headers,
        )
        remaining = client.get(f"/api/projects/{project['id']}/environments", headers=headers).json()

        assert updated.json()["variables"] == {"version": 2}
        assert deleted.status_code == 200
        assert remaining == [{**remaining[0], "id": second["id"], "is_active": True}]


def test_environment_requires_existing_project():
    with TestClient(app) as client:
        headers = auth_headers(client)
        response = client.post(
            "/api/projects/999999/environments",
            json={"name": "不存在"},
            headers=headers,
        )
    assert response.status_code == 404
