from unittest.mock import patch

import pytest

from app.config import settings
from app.services import strava as strava_service


class TestBuildAuthorizationUrl:
    def test_contains_required_params(self, monkeypatch):
        monkeypatch.setattr(settings, "strava_client_id", "test-strava-id")
        monkeypatch.setattr(settings, "strava_redirect_uri", "https://rowapp.example.com/api/integrations/strava/callback")

        url = strava_service.build_authorization_url("test-state-123")
        assert "www.strava.com/oauth/authorize" in url
        assert "client_id=test-strava-id" in url
        assert "redirect_uri=https%3A%2F%2Frowapp.example.com%2Fapi%2Fintegrations%2Fstrava%2Fcallback" in url
        assert "response_type=code" in url
        assert "scope=activity%3Aread_all" in url
        assert "state=test-state-123" in url

    def test_approval_prompt_default(self, monkeypatch):
        monkeypatch.setattr(settings, "strava_client_id", "id")
        monkeypatch.setattr(settings, "strava_approval_prompt", "auto")

        url = strava_service.build_authorization_url("state")
        assert "approval_prompt=auto" in url

    def test_approval_prompt_force(self, monkeypatch):
        monkeypatch.setattr(settings, "strava_client_id", "id")
        monkeypatch.setattr(settings, "strava_approval_prompt", "force")

        url = strava_service.build_authorization_url("state")
        assert "approval_prompt=force" in url


class TestExchangeCodeForToken:
    @patch("app.services.strava._post_form")
    def test_exchange_code(self, mock_post_form, monkeypatch):
        monkeypatch.setattr(settings, "strava_client_id", "id")
        monkeypatch.setattr(settings, "strava_client_secret", "secret")
        mock_post_form.return_value = {"access_token": "tok", "refresh_token": "rtok"}

        result = strava_service.exchange_code_for_token("code123")
        assert result["access_token"] == "tok"
        assert mock_post_form.call_args[0][0] == "https://www.strava.com/oauth/token"
        assert mock_post_form.call_args[0][1]["grant_type"] == "authorization_code"
        assert mock_post_form.call_args[0][1]["code"] == "code123"


class TestRefreshAccessToken:
    @patch("app.services.strava._post_form")
    def test_refresh_token(self, mock_post_form, monkeypatch):
        monkeypatch.setattr(settings, "strava_client_id", "id")
        monkeypatch.setattr(settings, "strava_client_secret", "secret")
        mock_post_form.return_value = {"access_token": "new_tok"}

        result = strava_service.refresh_access_token("old_refresh")
        assert result["access_token"] == "new_tok"
        assert mock_post_form.call_args[0][1]["grant_type"] == "refresh_token"
        assert mock_post_form.call_args[0][1]["refresh_token"] == "old_refresh"


class TestFetchAthleteActivities:
    @patch("app.services.strava._get")
    def test_default_params(self, mock_get):
        mock_get.return_value = []
        result = strava_service.fetch_athlete_activities("tok")
        assert result == []
        called_url = mock_get.call_args[0][0]
        assert "/athlete/activities" in called_url
        assert "page=1" in called_url
        assert "per_page=100" in called_url

    @patch("app.services.strava._get")
    def test_custom_per_page(self, mock_get):
        mock_get.return_value = [{"id": 1}]
        result = strava_service.fetch_athlete_activities("tok", per_page=50)
        assert len(result) == 1
        called_url = mock_get.call_args[0][0]
        assert "page=1" in called_url
        assert "per_page=50" in called_url

    @patch("app.services.strava._get")
    def test_non_list_response_raises(self, mock_get):
        mock_get.return_value = {"error": "rate limit"}
        with pytest.raises(strava_service.StravaAPIError, match="Expected list"):
            strava_service.fetch_athlete_activities("tok")


class TestFetchActivities:
    @patch("app.services.strava._get")
    def test_single_page(self, mock_get):
        mock_get.return_value = [{"id": 1}, {"id": 2}]
        result = strava_service.fetch_activities("tok", per_page=100, max_pages=5)
        assert len(result) == 2
        assert mock_get.call_count == 1

    @patch("app.services.strava._get")
    def test_paginates_across_multiple_pages(self, mock_get):
        mock_get.side_effect = [
            [{"id": i} for i in range(100)],
            [{"id": i} for i in range(100, 150)],
        ]
        result = strava_service.fetch_activities("tok", per_page=100, max_pages=5)
        assert len(result) == 150
        assert mock_get.call_count == 2

    @patch("app.services.strava._get")
    def test_stops_at_max_pages(self, mock_get):
        mock_get.side_effect = [
            [{"id": i} for i in range(100)] for _ in range(5)
        ]
        result = strava_service.fetch_activities("tok", per_page=100, max_pages=3)
        assert len(result) == 300
        assert mock_get.call_count == 3

    @patch("app.services.strava._get")
    def test_stops_early_on_short_page(self, mock_get):
        mock_get.side_effect = [
            [{"id": i} for i in range(100)],
            [{"id": i} for i in range(30)],
            [{"id": 1}],
        ]
        result = strava_service.fetch_activities("tok", per_page=100, max_pages=5)
        assert len(result) == 130
        assert mock_get.call_count == 2

    @patch("app.services.strava._get")
    def test_includes_after_param(self, mock_get):
        mock_get.return_value = []
        strava_service.fetch_activities("tok", after=1718000000)
        called_url = mock_get.call_args[0][0]
        assert "after=1718000000" in called_url

    @patch("app.services.strava._get")
    def test_non_list_raises(self, mock_get):
        mock_get.return_value = {"error": "rate limit"}
        with pytest.raises(strava_service.StravaAPIError, match="Expected list"):
            strava_service.fetch_activities("tok")

    @patch("app.services.strava._get")
    def test_uses_settings_api_base(self, mock_get, monkeypatch):
        monkeypatch.setattr(settings, "strava_api_base_url", "https://custom.api.com/v4")
        mock_get.return_value = []
        strava_service.fetch_activities("tok")
        called_url = mock_get.call_args[0][0]
        assert called_url.startswith("https://custom.api.com/v4")


class TestStravaAPIError:
    def test_is_exception(self):
        with pytest.raises(strava_service.StravaAPIError):
            raise strava_service.StravaAPIError("test error")
