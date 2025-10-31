import os
os.environ["DATABASE_DSN"] = "sqlite:///:memory:"

from fastapi.testclient import TestClient
from app import app
from utils.db import init_database


def setup_module(module):
    init_database()


def test_health():
    client = TestClient(app)
    r = client.get("/health")
    assert r.status_code == 200


def test_crud_endpoint():
    client = TestClient(app)

    # create
    payload = {"hostname": "host1", "ip": "10.0.0.1", "os": "Windows"}
    r = client.post("/api/endpoints/", json=payload)
    assert r.status_code == 201, r.text
    eid = r.json()["id"]

    # list
    r = client.get("/api/endpoints/")
    assert r.status_code == 200
    assert len(r.json()) == 1

    # get
    r = client.get(f"/api/endpoints/{eid}")
    assert r.status_code == 200

    # patch
    r = client.patch(f"/api/endpoints/{eid}", json={"status": "inactive"})
    assert r.status_code == 200
    assert r.json()["status"] == "inactive"

    # delete
    r = client.delete(f"/api/endpoints/{eid}")
    assert r.status_code == 204

    # verify empty
    r = client.get("/api/endpoints/")
    assert r.status_code == 200
    assert len(r.json()) == 0
