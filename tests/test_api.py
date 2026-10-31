import pytest
from fastapi.testclient import TestClient
from main import app
from database import Base, engine

@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    Base.metadata.create_all(bind=engine)
    yield

@pytest.fixture
def client():
    return TestClient(app)

def test_healthz_endpoint(client):
    response = client.get("/healthz")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "telecom-nms-backend"

def test_list_cell_sites(client):
    response = client.get("/api/v1/sites")
    assert response.status_code == 200
    sites = response.json()
    assert isinstance(sites, list)
    assert len(sites) >= 1

def test_create_and_get_site(client):
    new_site = {
        "site_code": "TEST-LTE-9999",
        "site_name": "Automated CI Test Cell",
        "region": "East Africa",
        "technology": "4G-LTE",
        "ip_address": "10.200.99.1"
    }
    create_res = client.post("/api/v1/sites", json=new_site)
    assert create_res.status_code == 201
    site_id = create_res.json()["id"]

    get_res = client.get(f"/api/v1/sites/{site_id}")
    assert get_res.status_code == 200
    assert get_res.json()["site_code"] == "TEST-LTE-9999"

def test_alarms_flow(client):
    # Fetch existing sites to link alarm
    sites = client.get("/api/v1/sites").json()
    first_site = sites[0]

    alarm_payload = {
        "site_id": first_site["id"],
        "site_code": first_site["site_code"],
        "severity": "CRITICAL",
        "alarm_type": "TEST_FAULT",
        "title": "CI/CD Test Optical Link Degradation"
    }
    alarm_res = client.post("/api/v1/alarms", json=alarm_payload)
    assert alarm_res.status_code == 201
    alarm_id = alarm_res.json()["id"]

    # Acknowledge alarm
    ack_res = client.post(f"/api/v1/alarms/{alarm_id}/ack?operator=CI_RUNNER")
    assert ack_res.status_code == 200
    assert ack_res.json()["is_acknowledged"] is True
    assert ack_res.json()["acknowledged_by"] == "CI_RUNNER"
