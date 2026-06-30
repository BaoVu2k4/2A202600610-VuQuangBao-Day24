from fastapi.testclient import TestClient

from src.api.main import app


client = TestClient(app)


def auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def test_raw_patients_only_admin_can_read():
    assert client.get("/api/patients/raw", headers=auth("token-alice")).status_code == 200
    assert client.get("/api/patients/raw", headers=auth("token-bob")).status_code == 403
    assert client.get("/api/patients/raw", headers=auth("token-carol")).status_code == 403
    assert client.get("/api/patients/raw", headers=auth("token-dave")).status_code == 403


def test_anonymized_patients_admin_and_ml_engineer_can_read():
    assert client.get("/api/patients/anonymized", headers=auth("token-alice")).status_code == 200
    assert client.get("/api/patients/anonymized", headers=auth("token-bob")).status_code == 200
    assert client.get("/api/patients/anonymized", headers=auth("token-carol")).status_code == 403
    assert client.get("/api/patients/anonymized", headers=auth("token-dave")).status_code == 403


def test_aggregated_metrics_for_admin_ml_engineer_and_analyst():
    assert client.get("/api/metrics/aggregated", headers=auth("token-alice")).status_code == 200
    assert client.get("/api/metrics/aggregated", headers=auth("token-bob")).status_code == 200
    assert client.get("/api/metrics/aggregated", headers=auth("token-carol")).status_code == 200
    assert client.get("/api/metrics/aggregated", headers=auth("token-dave")).status_code == 403


def test_delete_patient_is_admin_only():
    assert client.delete("/api/patients/not-found", headers=auth("token-alice")).status_code == 404
    assert client.delete("/api/patients/not-found", headers=auth("token-bob")).status_code == 403


def test_invalid_or_missing_token_is_unauthorized():
    assert client.get("/api/patients/raw").status_code == 401
    assert client.get("/api/patients/raw", headers=auth("bad-token")).status_code == 401
