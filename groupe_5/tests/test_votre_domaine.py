from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health_check() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_votre_domaine() -> None:
    response = client.get("/api/votre-domaine")
    assert response.status_code == 200
    assert response.json() == {"message": "Endpoint votre_domaine pret"}
