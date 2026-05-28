import secrets
from datetime import datetime, timedelta
from unittest.mock import patch

import pytest
from cryptography.fernet import Fernet
from fastapi.testclient import TestClient

from app.config import settings
from app.models.integration import OAuthState, StravaConnection
from app.models.user import User
from app.models.workout import Workout, WorkoutSource
from app.services.token_crypto import encrypt_with_key

VALID_KEY = Fernet.generate_key().decode()


@pytest.fixture(autouse=True)
def _crypto_key(monkeypatch):
    monkeypatch.setattr(settings, "strava_token_encryption_key", VALID_KEY)


def _create_state(db, user: User) -> str:
    state = secrets.token_urlsafe(32)
    oauth_state = OAuthState(
        user_id=user.id,
        provider="strava",
        state=state,
        expires_at=datetime.utcnow() + timedelta(minutes=10),
    )
    db.add(oauth_state)
    db.commit()
    return state


def _create_connection(db, user: User, expires_at=None) -> StravaConnection:
    conn = StravaConnection(
        user_id=user.id,
        strava_athlete_id="12345678",
        access_token_encrypted=encrypt_with_key("test_access_token", VALID_KEY),
        refresh_token_encrypted=encrypt_with_key("test_refresh_token", VALID_KEY),
        scope="activity:read_all",
        token_expires_at=expires_at,
    )
    db.add(conn)
    db.commit()
    return conn


class TestGetStatus:
    def test_requires_auth(self, client: TestClient):
        resp = client.get("/api/integrations/strava/status")
        assert resp.status_code in (401, 403)

    def test_returns_not_connected(self, client: TestClient, token_headers: dict):
        resp = client.get("/api/integrations/strava/status", headers=token_headers)
        assert resp.status_code == 200
        assert resp.json()["connected"] is False

    def test_returns_connected(self, client: TestClient, token_headers: dict, db, user_on_team: User):
        _create_connection(db, user_on_team)
        resp = client.get("/api/integrations/strava/status", headers=token_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["connected"] is True
        assert data["strava_athlete_id"] == "12345678"


class TestConnect:
    def test_requires_auth(self, client: TestClient):
        resp = client.post("/api/integrations/strava/connect")
        assert resp.status_code in (401, 403)

    def test_missing_oauth_client_id_returns_configuration_error(self, client: TestClient, token_headers: dict, monkeypatch):
        monkeypatch.setattr(settings, "strava_client_id", "")

        resp = client.post("/api/integrations/strava/connect", headers=token_headers)

        assert resp.status_code == 500
        assert "Strava OAuth is not configured" in resp.json()["detail"]

    def test_missing_oauth_client_secret_returns_configuration_error(self, client: TestClient, token_headers: dict, monkeypatch):
        monkeypatch.setattr(settings, "strava_client_id", "test-strava-id")
        monkeypatch.setattr(settings, "strava_client_secret", "")

        resp = client.post("/api/integrations/strava/connect", headers=token_headers)

        assert resp.status_code == 500
        assert "Strava OAuth is not configured" in resp.json()["detail"]

    def test_creates_oauth_state_and_returns_url(self, client: TestClient, token_headers: dict, db, user_on_team: User, monkeypatch):
        monkeypatch.setattr(settings, "strava_client_id", "test-strava-id")
        monkeypatch.setattr(settings, "strava_client_secret", "test-strava-secret")
        monkeypatch.setattr(settings, "strava_redirect_uri", "https://rowapp.example.com/api/integrations/strava/callback")

        resp = client.post("/api/integrations/strava/connect", headers=token_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "authorization_url" in data
        assert "www.strava.com/oauth/authorize" in data["authorization_url"]
        assert "client_id=test-strava-id" in data["authorization_url"]
        assert "scope=activity%3Aread_all" in data["authorization_url"]

        state_count = db.query(OAuthState).filter(
            OAuthState.user_id == user_on_team.id,
            OAuthState.provider == "strava",
        ).count()
        assert state_count == 1

    def test_auth_url_contains_required_scope(self, client: TestClient, token_headers: dict, db, user_on_team: User, monkeypatch):
        monkeypatch.setattr(settings, "strava_client_id", "test-strava-id")
        monkeypatch.setattr(settings, "strava_client_secret", "test-strava-secret")

        resp = client.post("/api/integrations/strava/connect", headers=token_headers)
        assert resp.status_code == 200
        assert "activity%3Aread_all" in resp.json()["authorization_url"]


class TestCallback:
    def test_missing_state_returns_422(self, client: TestClient):
        resp = client.get("/api/integrations/strava/callback")
        assert resp.status_code == 422

    def test_missing_code_returns_error(self, client: TestClient):
        resp = client.get("/api/integrations/strava/callback?state=abc")
        assert resp.status_code == 400
        assert "Missing authorization code" in resp.text

    def test_invalid_state_returns_error_html(self, client: TestClient):
        resp = client.get("/api/integrations/strava/callback?state=invalid&code=testcode&scope=activity:read_all")
        assert resp.status_code == 400
        assert "Invalid state" in resp.text

    def test_expired_state_returns_error_html(self, client: TestClient, db, user_on_team: User):
        state = secrets.token_urlsafe(32)
        expired = OAuthState(
            user_id=user_on_team.id,
            provider="strava",
            state=state,
            expires_at=datetime.utcnow() - timedelta(minutes=1),
        )
        db.add(expired)
        db.commit()

        resp = client.get(f"/api/integrations/strava/callback?state={state}&code=testcode&scope=activity:read_all")
        assert resp.status_code == 400
        assert "expired" in resp.text.lower()

    def test_consumed_state_returns_error_html(self, client: TestClient, db, user_on_team: User):
        state = _create_state(db, user_on_team)
        oauth_state = db.query(OAuthState).filter(OAuthState.state == state).first()
        oauth_state.consumed_at = datetime.utcnow()
        db.commit()

        resp = client.get(f"/api/integrations/strava/callback?state={state}&code=testcode&scope=activity:read_all")
        assert resp.status_code == 400
        assert "already been used" in resp.text.lower()

    def test_strava_denial_returns_error_html(self, client: TestClient):
        resp = client.get("/api/integrations/strava/callback?state=abc&code=testcode&error=access_denied")
        assert resp.status_code == 400
        assert "denied" in resp.text.lower()

    def test_missing_required_scope_returns_error(self, client: TestClient, db, user_on_team: User):
        state = _create_state(db, user_on_team)
        resp = client.get(
            f"/api/integrations/strava/callback?state={state}&code=testcode&scope=activity:read"
        )
        assert resp.status_code == 400
        assert "Required scope" in resp.text
        assert "activity:read_all" in resp.text

    def test_no_scope_at_all_returns_error(self, client: TestClient, db, user_on_team: User):
        state = _create_state(db, user_on_team)
        resp = client.get(
            f"/api/integrations/strava/callback?state={state}&code=testcode"
        )
        assert resp.status_code == 400
        assert "Required scope" in resp.text

    def test_scope_exact_match_with_extra_scopes(self, client: TestClient, db, user_on_team: User):
        state = _create_state(db, user_on_team)
        resp = client.get(
            f"/api/integrations/strava/callback?state={state}&code=testcode"
            f"&scope=activity:read_all,activity:read,read"
        )
        assert resp.status_code in (200, 400)

    def test_scope_substring_does_not_match(self, client: TestClient, db, user_on_team: User):
        state = _create_state(db, user_on_team)
        resp = client.get(
            f"/api/integrations/strava/callback?state={state}&code=testcode"
            f"&scope=extra_activity:read_all"
        )
        assert resp.status_code == 400
        assert "Required scope" in resp.text

    def test_scope_missing_from_comma_list_returns_error(self, client: TestClient, db, user_on_team: User):
        state = _create_state(db, user_on_team)
        resp = client.get(
            f"/api/integrations/strava/callback?state={state}&code=testcode"
            f"&scope=activity:read,read,write"
        )
        assert resp.status_code == 400
        assert "Required scope" in resp.text

    @patch("app.services.strava.exchange_code_for_token")
    def test_success_creates_connection_and_consumes_state(
        self, mock_exchange, client: TestClient, db, user_on_team: User,
    ):
        state = _create_state(db, user_on_team)
        mock_exchange.return_value = {
            "access_token": "real_access_token",
            "refresh_token": "real_refresh_token",
            "expires_in": 21600,
            "expires_at": 1900000000,
            "athlete": {"id": 12345678, "firstname": "Test", "lastname": "Rower"},
        }

        resp = client.get(
            f"/api/integrations/strava/callback?state={state}&code=validcode&scope=activity:read_all"
        )
        assert resp.status_code == 200
        assert "Connected" in resp.text

        oauth_state = db.query(OAuthState).filter(OAuthState.state == state).first()
        assert oauth_state.consumed_at is not None

        conn = db.query(StravaConnection).filter(
            StravaConnection.user_id == user_on_team.id,
        ).first()
        assert conn is not None
        assert conn.strava_athlete_id == "12345678"
        assert conn.scope == "activity:read_all"
        assert conn.token_expires_at is not None

    @patch("app.services.strava.exchange_code_for_token")
    def test_success_uses_expires_at_when_present(
        self, mock_exchange, client: TestClient, db, user_on_team: User,
    ):
        state = _create_state(db, user_on_team)
        mock_exchange.return_value = {
            "access_token": "real_access_token",
            "refresh_token": "real_refresh_token",
            "expires_in": 21600,
            "expires_at": 1900000000,
            "athlete": {"id": 87654321},
        }

        resp = client.get(
            f"/api/integrations/strava/callback?state={state}&code=validcode&scope=activity:read_all"
        )
        assert resp.status_code == 200

        conn = db.query(StravaConnection).filter(
            StravaConnection.user_id == user_on_team.id,
        ).first()
        from datetime import datetime, timezone
        expected = datetime.fromtimestamp(1900000000, tz=timezone.utc).replace(tzinfo=None)
        assert conn.token_expires_at == expected

    @patch("app.services.strava.exchange_code_for_token")
    def test_success_falls_back_to_expires_in(
        self, mock_exchange, client: TestClient, db, user_on_team: User,
    ):
        state = _create_state(db, user_on_team)
        mock_exchange.return_value = {
            "access_token": "tok",
            "refresh_token": "rtok",
            "expires_in": 21600,
            "athlete": {"id": 11111111},
        }

        resp = client.get(
            f"/api/integrations/strava/callback?state={state}&code=validcode&scope=activity:read_all"
        )
        assert resp.status_code == 200

        conn = db.query(StravaConnection).filter(
            StravaConnection.user_id == user_on_team.id,
        ).first()
        assert conn.token_expires_at is not None

    @patch("app.services.strava.exchange_code_for_token")
    def test_exchange_failure_returns_error_html(
        self, mock_exchange, client: TestClient, db, user_on_team: User,
    ):
        state = _create_state(db, user_on_team)
        mock_exchange.side_effect = Exception("Network error")

        resp = client.get(
            f"/api/integrations/strava/callback?state={state}&code=badcode&scope=activity:read_all"
        )
        assert resp.status_code == 400
        assert "failed" in resp.text.lower()


class TestSync:
    def test_requires_auth(self, client: TestClient):
        resp = client.post("/api/integrations/strava/sync")
        assert resp.status_code in (401, 403)

    def test_no_connection_returns_400(self, client: TestClient, token_headers: dict):
        resp = client.post("/api/integrations/strava/sync", headers=token_headers)
        assert resp.status_code == 400
        assert "connect" in resp.json()["detail"].lower()

    @patch("app.services.strava.fetch_activities")
    def test_sync_imports_rowing_only(
        self, mock_fetch, client: TestClient, token_headers: dict, db, user_on_team: User,
    ):
        _create_connection(db, user_on_team)
        mock_fetch.return_value = [
            {
                "id": 1001,
                "sport_type": "Rowing",
                "start_date": "2026-05-24T12:00:00Z",
                "name": "Morning Row",
                "moving_time": 1800,
                "distance": 5000.0,
            },
            {
                "id": 2001,
                "sport_type": "Run",
                "start_date": "2026-05-24T14:00:00Z",
                "name": "Afternoon Run",
                "moving_time": 2400,
                "distance": 8000.0,
            },
            {
                "id": 2002,
                "sport_type": "Ride",
                "start_date": "2026-05-25T10:00:00Z",
                "name": "Morning Ride",
                "elapsed_time": 3600,
                "distance": 30000.0,
            },
        ]

        resp = client.post("/api/integrations/strava/sync", headers=token_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["imported"] == 1
        assert data["skipped"] == 2
        assert data["errors"] == []

        workout = db.query(Workout).filter(
            Workout.user_id == user_on_team.id,
            Workout.source == WorkoutSource.STRAVA,
        ).first()
        assert workout is not None
        assert workout.source_id == "1001"
        assert workout.workout_name == "Morning Row"

    @patch("app.services.strava.fetch_activities")
    def test_sync_skips_non_rowing_and_returns_counts(
        self, mock_fetch, client: TestClient, token_headers: dict, db, user_on_team: User,
    ):
        _create_connection(db, user_on_team)
        mock_fetch.return_value = [
            {
                "id": 2001,
                "sport_type": "Run",
                "start_date": "2026-05-24T14:00:00Z",
                "name": "Run",
                "moving_time": 2400,
                "distance": 8000.0,
            },
        ]

        resp = client.post("/api/integrations/strava/sync", headers=token_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["imported"] == 0
        assert data["skipped"] == 1
        assert data["errors"] == []

        count = db.query(Workout).filter(
            Workout.user_id == user_on_team.id,
            Workout.source == WorkoutSource.STRAVA,
        ).count()
        assert count == 0

    @patch("app.services.strava.fetch_activities")
    def test_sync_no_fallback_to_deprecated_type(
        self, mock_fetch, client: TestClient, token_headers: dict, db, user_on_team: User,
    ):
        _create_connection(db, user_on_team)
        mock_fetch.return_value = [
            {
                "id": 3001,
                "type": "Rowing",
                "sport_type": None,
                "start_date": "2026-05-24T12:00:00Z",
                "name": "No Sport Type",
                "moving_time": 1800,
                "distance": 5000.0,
            },
        ]

        resp = client.post("/api/integrations/strava/sync", headers=token_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["imported"] == 0
        assert data["skipped"] == 1

    @patch("app.services.strava.fetch_activities")
    def test_sync_private_default(
        self, mock_fetch, client: TestClient, token_headers: dict, db, user_on_team: User,
    ):
        _create_connection(db, user_on_team)
        mock_fetch.return_value = [
            {
                "id": 1002,
                "sport_type": "Rowing",
                "start_date": "2026-05-24T12:00:00Z",
                "name": "Private Row",
                "moving_time": 1800,
                "distance": 5000.0,
            },
        ]

        resp = client.post("/api/integrations/strava/sync", headers=token_headers)
        assert resp.status_code == 200

        workout = db.query(Workout).filter(
            Workout.user_id == user_on_team.id,
            Workout.source == WorkoutSource.STRAVA,
        ).first()
        assert workout.visibility == "private"

    @patch("app.services.strava.fetch_activities")
    def test_sync_idempotent_no_duplicates(
        self, mock_fetch, client: TestClient, token_headers: dict, db, user_on_team: User,
    ):
        _create_connection(db, user_on_team)
        mock_fetch.return_value = [
            {
                "id": 1001,
                "sport_type": "Rowing",
                "start_date": "2026-05-24T12:00:00Z",
                "name": "Morning Row",
                "moving_time": 1800,
                "distance": 5000.0,
            },
        ]

        resp1 = client.post("/api/integrations/strava/sync", headers=token_headers)
        assert resp1.json()["imported"] == 1

        resp2 = client.post("/api/integrations/strava/sync", headers=token_headers)
        assert resp2.json()["imported"] == 0
        assert resp2.json()["updated"] == 1

        count = db.query(Workout).filter(
            Workout.user_id == user_on_team.id,
            Workout.source == WorkoutSource.STRAVA,
        ).count()
        assert count == 1

    @patch("app.services.strava.fetch_activities")
    def test_sync_updates_last_sync_at(
        self, mock_fetch, client: TestClient, token_headers: dict, db, user_on_team: User,
    ):
        conn = _create_connection(db, user_on_team)
        mock_fetch.return_value = []

        resp = client.post("/api/integrations/strava/sync", headers=token_headers)
        assert resp.status_code == 200

        db.refresh(conn)
        assert conn.last_sync_at is not None

    @patch("app.services.strava.refresh_access_token")
    @patch("app.services.strava.fetch_activities")
    def test_sync_refreshes_token_near_expiry(
        self, mock_fetch, mock_refresh, client: TestClient, token_headers: dict, db, user_on_team: User,
    ):
        near_expiry = datetime.utcnow() + timedelta(minutes=2)
        _create_connection(db, user_on_team, expires_at=near_expiry)
        mock_fetch.return_value = []
        mock_refresh.return_value = {
            "access_token": "new_access_token",
            "refresh_token": "new_refresh_token",
            "expires_in": 21600,
            "expires_at": 1900000000,
        }

        resp = client.post("/api/integrations/strava/sync", headers=token_headers)
        assert resp.status_code == 200

    @patch("app.services.strava.refresh_access_token")
    @patch("app.services.strava.fetch_activities")
    def test_sync_token_refresh_falls_back_to_expires_in(
        self, mock_fetch, mock_refresh, client: TestClient, token_headers: dict, db, user_on_team: User,
    ):
        near_expiry = datetime.utcnow() + timedelta(minutes=2)
        _create_connection(db, user_on_team, expires_at=near_expiry)
        mock_fetch.return_value = []
        mock_refresh.return_value = {
            "access_token": "new_access_token",
            "refresh_token": "new_refresh_token",
            "expires_in": 21600,
        }

        resp = client.post("/api/integrations/strava/sync", headers=token_headers)
        assert resp.status_code == 200


class TestDisconnect:
    def test_requires_auth(self, client: TestClient):
        resp = client.post("/api/integrations/strava/disconnect")
        assert resp.status_code in (401, 403)

    def test_no_connection_returns_404(self, client: TestClient, token_headers: dict):
        resp = client.post("/api/integrations/strava/disconnect", headers=token_headers)
        assert resp.status_code == 404

    def test_disconnect_removes_connection(self, client: TestClient, token_headers: dict, db, user_on_team: User):
        _create_connection(db, user_on_team)
        resp = client.post("/api/integrations/strava/disconnect", headers=token_headers)
        assert resp.status_code == 200

        conn_count = db.query(StravaConnection).filter(
            StravaConnection.user_id == user_on_team.id,
        ).count()
        assert conn_count == 0

    def test_disconnect_keeps_workouts(self, client: TestClient, token_headers: dict, db, user_on_team: User):
        _create_connection(db, user_on_team)
        workout = Workout(
            user_id=user_on_team.id,
            source=WorkoutSource.STRAVA,
            source_id="existing",
            workout_date=datetime.utcnow(),
            duration_seconds=1800,
            distance_meters=5000,
            visibility="private",
        )
        db.add(workout)
        db.commit()

        resp = client.post("/api/integrations/strava/disconnect", headers=token_headers)
        assert resp.status_code == 200
        assert "kept" in resp.json()["message"].lower()

        workout_count = db.query(Workout).filter(
            Workout.user_id == user_on_team.id,
            Workout.source == WorkoutSource.STRAVA,
        ).count()
        assert workout_count == 1
