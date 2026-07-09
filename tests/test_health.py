from fastapi.testclient import TestClient

from app.main import app


def test_health():
    with TestClient(app) as client:
        response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_home_page():
    with TestClient(app) as client:
        response = client.get("/")
    assert response.status_code == 200
    assert "TestPilot" in response.text
    assert "接口自动化测试平台" in response.text
