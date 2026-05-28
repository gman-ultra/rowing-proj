from app.config import Settings


class TestConcept2Config:
    def test_defaults_empty(self, monkeypatch):
        monkeypatch.setitem(Settings.model_config, "env_file", None)
        s = Settings()
        assert s.concept2_client_id == ""
        assert s.concept2_client_secret == ""
        assert s.concept2_token_encryption_key == ""
        assert s.concept2_base_url == "https://log.concept2.com"

    def test_default_redirect_uri(self, monkeypatch):
        monkeypatch.setitem(Settings.model_config, "env_file", None)
        s = Settings()
        expected = "http://localhost:8000/api/integrations/concept2/callback"
        assert s.concept2_redirect_uri == expected

    def test_reads_env_vars(self, monkeypatch):
        monkeypatch.setenv("CONCEPT2_CLIENT_ID", "test-client-id")
        monkeypatch.setenv("CONCEPT2_CLIENT_SECRET", "test-client-secret")
        monkeypatch.setenv("CONCEPT2_REDIRECT_URI", "https://rowapp.example.com/api/integrations/concept2/callback")
        monkeypatch.setenv("CONCEPT2_TOKEN_ENCRYPTION_KEY", "test-encryption-key")
        s = Settings()
        assert s.concept2_client_id == "test-client-id"
        assert s.concept2_client_secret == "test-client-secret"
        assert s.concept2_redirect_uri == "https://rowapp.example.com/api/integrations/concept2/callback"
        assert s.concept2_token_encryption_key == "test-encryption-key"

    def test_base_url_override(self, monkeypatch):
        monkeypatch.setenv("CONCEPT2_BASE_URL", "https://custom.log.concept2.com")
        s = Settings()
        assert s.concept2_base_url == "https://custom.log.concept2.com"
