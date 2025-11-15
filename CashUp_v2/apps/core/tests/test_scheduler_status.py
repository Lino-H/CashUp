import pytest
from fastapi.testclient import TestClient
from apps.core.main import app


def test_scheduler_status_endpoint():
    client = TestClient(app)
    r = client.get("/api/v1/scheduler/status?granularity=hour")
    assert r.status_code == 200
    data = r.json()
    assert data.get("code") == 0
    assert "data" in data