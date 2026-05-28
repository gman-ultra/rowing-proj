import secrets
from datetime import datetime, timedelta
from unittest.mock import patch

import pytest
from cryptography.fernet import Fernet
from fastapi.testclient import TestClient

from app.config import settings
from app.models.integration import Concept2Connection, OAuthState
from app.models.user import User
from app.models.workout import Workout, WorkoutSource
from app.services.token_crypto import encrypt_token

VALID_KEY = Fernet.generate_key().decode()


@pytest.fixture(autouse=True)
def _crypto_key(monkeypatch):
    monkeypatch.setattr(settings, "concept2_token_encryption_key", VALID_KEY)


def _create_state(db, user: User) -> str:
    state = secrets.token_urlsafe(32)
    oauth_state = OAuthState(
        user_id=user.id,
        provider="concept2",
        state=state,
        expires_at=datetime.utcnow() + timedelta(minutes=10),
    )
    db.add(oauth_state)
    db.commit()
    return state


def _create_connection(db, user: User) -> Concept2Connection:
    conn = Concept2Connection(
        user_id=user.id,
        concept2_user_id="1591266",
        access_token_encrypted=encrypt_token("test_access_token"),
        refresh_token_encrypted=encrypt_token("test_refresh_token"),
        scope="results:read",
    )
    db.add(conn)
    db.commit()
    return conn


class TestGetStatus:
    def test_requires_auth(self, client: TestClient):
        resp = client.get("/api/integrations/concept2/status")
        assert resp.status_code in (401, 403)

    def test_returns_not_connected(self, client: TestClient, token_headers: dict):
        resp = client.get("/api/integrations/concept2/status", headers=token_headers)
        assert resp.status_code == 200
        assert resp.json()["connected"] is False

    def test_returns_connected(self, client: TestClient, token_headers: dict, db, user_on_team: User):
        _create_connection(db, user_on_team)
        resp = client.get("/api/integrations/concept2/status", headers=token_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["connected"] is True
        assert data["concept2_user_id"] == "1591266"


class TestConnect:
    def test_requires_auth(self, client: TestClient):
        resp = client.post("/api/integrations/concept2/connect")
        assert resp.status_code in (401, 403)

    def test_missing_oauth_client_id_returns_configuration_error(self, client: TestClient, token_headers: dict, monkeypatch):
        monkeypatch.setattr(settings, "concept2_client_id", "")

        resp = client.post("/api/integrations/concept2/connect", headers=token_headers)

        assert resp.status_code == 500
        assert "Concept2 OAuth is not configured" in resp.json()["detail"]

    def test_missing_oauth_client_secret_returns_configuration_error(self, client: TestClient, token_headers: dict, monkeypatch):
        monkeypatch.setattr(settings, "concept2_client_id", "test-client-id")
        monkeypatch.setattr(settings, "concept2_client_secret", "")

        resp = client.post("/api/integrations/concept2/connect", headers=token_headers)

        assert resp.status_code == 500
        assert "Concept2 OAuth is not configured" in resp.json()["detail"]

    def test_creates_oauth_state_and_returns_url(self, client: TestClient, token_headers: dict, db, user_on_team: User, monkeypatch):
        monkeypatch.setattr(settings, "concept2_client_id", "test-client-id")
        monkeypatch.setattr(settings, "concept2_client_secret", "test-client-secret")
        monkeypatch.setattr(settings, "concept2_redirect_uri", "https://rowapp.example.com/api/integrations/concept2/callback")

        resp = client.post("/api/integrations/concept2/connect", headers=token_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "authorization_url" in data
        assert "log.concept2.com/oauth/authorize" in data["authorization_url"]
        assert "client_id=test-client-id" in data["authorization_url"]
        assert "localhost" not in data["authorization_url"]

        state_count = db.query(OAuthState).filter(
            OAuthState.user_id == user_on_team.id,
            OAuthState.provider == "concept2",
        ).count()
        assert state_count == 1


class TestCallback:
    def test_missing_state_returns_422(self, client: TestClient):
        resp = client.get("/api/integrations/concept2/callback")
        assert resp.status_code == 422

    def test_missing_code_returns_422(self, client: TestClient):
        resp = client.get("/api/integrations/concept2/callback?state=abc")
        assert resp.status_code == 422

    def test_invalid_state_returns_error_html(self, client: TestClient):
        resp = client.get("/api/integrations/concept2/callback?state=invalid&code=testcode")
        assert resp.status_code == 400
        assert "Invalid state" in resp.text

    def test_expired_state_returns_error_html(self, client: TestClient, db, user_on_team: User):
        state = secrets.token_urlsafe(32)
        expired = OAuthState(
            user_id=user_on_team.id,
            provider="concept2",
            state=state,
            expires_at=datetime.utcnow() - timedelta(minutes=1),
        )
        db.add(expired)
        db.commit()

        resp = client.get(f"/api/integrations/concept2/callback?state={state}&code=testcode")
        assert resp.status_code == 400
        assert "expired" in resp.text.lower()

    def test_consumed_state_returns_error_html(self, client: TestClient, db, user_on_team: User):
        state = _create_state(db, user_on_team)
        oauth_state = db.query(OAuthState).filter(OAuthState.state == state).first()
        oauth_state.consumed_at = datetime.utcnow()
        db.commit()

        resp = client.get(f"/api/integrations/concept2/callback?state={state}&code=testcode")
        assert resp.status_code == 400
        assert "already been used" in resp.text.lower()

    @patch("app.services.concept2.exchange_code_for_token")
    def test_success_creates_connection_and_consumes_state(
        self, mock_exchange, client: TestClient, db, user_on_team: User,
    ):
        state = _create_state(db, user_on_team)
        mock_exchange.return_value = {
            "access_token": "real_access_token",
            "refresh_token": "real_refresh_token",
            "expires_in": 3600,
            "scope": "results:read",
            "concept2_user_id": "1591266",
        }

        resp = client.get(f"/api/integrations/concept2/callback?state={state}&code=validcode")
        assert resp.status_code == 200
        assert "Connected" in resp.text

        oauth_state = db.query(OAuthState).filter(OAuthState.state == state).first()
        assert oauth_state.consumed_at is not None

        conn = db.query(Concept2Connection).filter(
            Concept2Connection.user_id == user_on_team.id,
        ).first()
        assert conn is not None
        assert conn.concept2_user_id == "1591266"

    @patch("app.services.concept2.exchange_code_for_token")
    def test_exchange_failure_returns_error_html(
        self, mock_exchange, client: TestClient, db, user_on_team: User,
    ):
        state = _create_state(db, user_on_team)
        mock_exchange.side_effect = Exception("Network error")

        resp = client.get(f"/api/integrations/concept2/callback?state={state}&code=badcode")
        assert resp.status_code == 400
        assert "failed" in resp.text.lower()


class TestSync:
    def test_requires_auth(self, client: TestClient):
        resp = client.post("/api/integrations/concept2/sync")
        assert resp.status_code in (401, 403)

    def test_no_connection_returns_400(self, client: TestClient, token_headers: dict):
        resp = client.post("/api/integrations/concept2/sync", headers=token_headers)
        assert resp.status_code == 400
        assert "connect" in resp.json()["detail"].lower()

    @patch("app.services.concept2.fetch_results")
    def test_sync_imports_workouts(
        self, mock_fetch, client: TestClient, token_headers: dict, db, user_on_team: User,
    ):
        _create_connection(db, user_on_team)
        mock_fetch.return_value = [
            {
                "id": 1001,
                "date": "2026-05-24",
                "date_utc": "2026-05-24T12:00:00Z",
                "time": 18000,
                "distance": 5000,
                "stroke_rate": 24,
                "calories_total": 350,
            },
        ]

        resp = client.post("/api/integrations/concept2/sync", headers=token_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["imported"] == 1
        assert data["errors"] == []

        workout = db.query(Workout).filter(
            Workout.user_id == user_on_team.id,
            Workout.source == WorkoutSource.CONCEPT2,
        ).first()
        assert workout is not None
        assert workout.source_id == "1001"
        assert workout.duration_seconds == 1800.0

    @patch("app.services.concept2.fetch_results")
    def test_sync_idempotent_no_duplicates(
        self, mock_fetch, client: TestClient, token_headers: dict, db, user_on_team: User,
    ):
        _create_connection(db, user_on_team)
        mock_fetch.return_value = [
            {
                "id": 1001,
                "date": "2026-05-24",
                "date_utc": "2026-05-24T12:00:00Z",
                "time": 18000,
                "distance": 5000,
            },
        ]

        resp1 = client.post("/api/integrations/concept2/sync", headers=token_headers)
        assert resp1.json()["imported"] == 1

        resp2 = client.post("/api/integrations/concept2/sync", headers=token_headers)
        assert resp2.json()["imported"] == 0
        assert resp2.json()["updated"] == 1

        count = db.query(Workout).filter(
            Workout.user_id == user_on_team.id,
            Workout.source == WorkoutSource.CONCEPT2,
        ).count()
        assert count == 1

    @patch("app.services.concept2.fetch_results")
    def test_sync_updates_last_sync_at(
        self, mock_fetch, client: TestClient, token_headers: dict, db, user_on_team: User,
    ):
        conn = _create_connection(db, user_on_team)
        mock_fetch.return_value = []

        resp = client.post("/api/integrations/concept2/sync", headers=token_headers)
        assert resp.status_code == 200

        db.refresh(conn)
        assert conn.last_sync_at is not None


class TestDisconnect:
    def test_requires_auth(self, client: TestClient):
        resp = client.post("/api/integrations/concept2/disconnect")
        assert resp.status_code in (401, 403)

    def test_no_connection_returns_404(self, client: TestClient, token_headers: dict):
        resp = client.post("/api/integrations/concept2/disconnect", headers=token_headers)
        assert resp.status_code == 404

    def test_disconnect_removes_connection(self, client: TestClient, token_headers: dict, db, user_on_team: User):
        _create_connection(db, user_on_team)
        resp = client.post("/api/integrations/concept2/disconnect", headers=token_headers)
        assert resp.status_code == 200

        conn_count = db.query(Concept2Connection).filter(
            Concept2Connection.user_id == user_on_team.id,
        ).count()
        assert conn_count == 0

    def test_disconnect_keeps_workouts(self, client: TestClient, token_headers: dict, db, user_on_team: User):
        conn = _create_connection(db, user_on_team)
        workout = Workout(
            user_id=user_on_team.id,
            source=WorkoutSource.CONCEPT2,
            source_id="existing",
            workout_date=datetime.utcnow(),
            duration_seconds=1800,
            distance_meters=5000,
            visibility="private",
        )
        db.add(workout)
        db.commit()

        resp = client.post("/api/integrations/concept2/disconnect", headers=token_headers)
        assert resp.status_code == 200
        assert "kept" in resp.json()["message"].lower()

        workout_count = db.query(Workout).filter(
            Workout.user_id == user_on_team.id,
            Workout.source == WorkoutSource.CONCEPT2,
        ).count()
        assert workout_count == 1
