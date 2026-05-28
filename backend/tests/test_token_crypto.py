import pytest
from cryptography.fernet import Fernet

from app.config import settings
from app.services.token_crypto import TokenEncryptionError, decrypt_token, encrypt_token

VALID_KEY = Fernet.generate_key().decode()


class TestTokenCrypto:
    def test_missing_key_raises_error(self, monkeypatch):
        monkeypatch.setattr(settings, "concept2_token_encryption_key", "")
        with pytest.raises(TokenEncryptionError, match="not configured"):
            encrypt_token("anything")

    def test_decrypt_with_missing_key_raises_error(self, monkeypatch):
        monkeypatch.setattr(settings, "concept2_token_encryption_key", "")
        with pytest.raises(TokenEncryptionError, match="not configured"):
            decrypt_token("anything")

    def test_encrypt_decrypt_roundtrip(self, monkeypatch):
        monkeypatch.setattr(settings, "concept2_token_encryption_key", VALID_KEY)
        plain = "my-super-secret-token-12345"
        encrypted = encrypt_token(plain)
        assert encrypted != plain
        assert encrypted != ""
        decrypted = decrypt_token(encrypted)
        assert decrypted == plain

    def test_encrypted_output_is_not_plaintext(self, monkeypatch):
        monkeypatch.setattr(settings, "concept2_token_encryption_key", VALID_KEY)
        plain = "test-token"
        encrypted = encrypt_token(plain)
        assert plain not in encrypted

    def test_decrypt_with_wrong_key_fails(self, monkeypatch):
        monkeypatch.setattr(settings, "concept2_token_encryption_key", VALID_KEY)
        plain = "secret"
        encrypted = encrypt_token(plain)

        other_key = Fernet.generate_key().decode()
        monkeypatch.setattr(settings, "concept2_token_encryption_key", other_key)
        with pytest.raises(Exception):
            decrypt_token(encrypted)

    def test_empty_string_roundtrip(self, monkeypatch):
        monkeypatch.setattr(settings, "concept2_token_encryption_key", VALID_KEY)
        encrypted = encrypt_token("")
        decrypted = decrypt_token(encrypted)
        assert decrypted == ""

    def test_long_token_roundtrip(self, monkeypatch):
        monkeypatch.setattr(settings, "concept2_token_encryption_key", VALID_KEY)
        plain = "a" * 5000
        encrypted = encrypt_token(plain)
        decrypted = decrypt_token(encrypted)
        assert decrypted == plain
