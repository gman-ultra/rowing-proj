from app.config import Settings


class TestStravaConfig:
    def test_defaults_empty(self, monkeypatch):
        monkeypatch.setitem(Settings.model_config, "env_file", None)
        s = Settings()
        assert s.strava_client_id == ""
        assert s.strava_client_secret == ""
        assert s.strava_token_encryption_key == ""
        assert s.strava_approval_prompt == "auto"
        assert s.strava_base_url == "https://www.strava.com"
        assert s.strava_api_base_url == "https://www.strava.com/api/v3"

    def test_default_redirect_uri(self, monkeypatch):
        monkeypatch.setitem(Settings.model_config, "env_file", None)
        s = Settings()
        expected = "http://localhost:8000/api/integrations/strava/callback"
        assert s.strava_redirect_uri == expected

    def test_reads_strava_base_url_env(self, monkeypatch):
        monkeypatch.setenv("STRAVA_BASE_URL", "https://custom.strava.example.com")
        monkeypatch.setitem(Settings.model_config, "env_file", None)
        s = Settings()
        assert s.strava_base_url == "https://custom.strava.example.com"

    def test_reads_strava_api_base_url_env(self, monkeypatch):
        monkeypatch.setenv("STRAVA_API_BASE_URL", "https://custom.api.example.com/v4")
        monkeypatch.setitem(Settings.model_config, "env_file", None)
        s = Settings()
        assert s.strava_api_base_url == "https://custom.api.example.com/v4"

    def test_reads_env_vars(self, monkeypatch):
        monkeypatch.setenv("STRAVA_CLIENT_ID", "test-strava-id")
        monkeypatch.setenv("STRAVA_CLIENT_SECRET", "test-strava-secret")
        monkeypatch.setenv("STRAVA_REDIRECT_URI", "https://rowapp.example.com/api/integrations/strava/callback")
        monkeypatch.setenv("STRAVA_TOKEN_ENCRYPTION_KEY", "test-encryption-key")
        monkeypatch.setenv("STRAVA_APPROVAL_PROMPT", "force")
        monkeypatch.setitem(Settings.model_config, "env_file", None)
        s = Settings()
        assert s.strava_client_id == "test-strava-id"
        assert s.strava_client_secret == "test-strava-secret"
        assert s.strava_redirect_uri == "https://rowapp.example.com/api/integrations/strava/callback"
        assert s.strava_token_encryption_key == "test-encryption-key"
        assert s.strava_approval_prompt == "force"
