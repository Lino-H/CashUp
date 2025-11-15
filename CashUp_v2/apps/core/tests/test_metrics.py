import pytest
from fastapi.testclient import TestClient
from apps.core.main import app


def test_metrics_endpoint_basic():
    client = TestClient(app)
    r = client.get("/metrics")
    assert r.status_code == 200
    body = r.text
    assert "cashup_sched_last_timestamp" in body