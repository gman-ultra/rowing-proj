from cryptography.fernet import Fernet

from app.config import settings


class TokenEncryptionError(Exception):
    pass


def _get_fernet() -> Fernet:
    key = settings.concept2_token_encryption_key
    if not key:
        raise TokenEncryptionError(
            "CONCEPT2_TOKEN_ENCRYPTION_KEY is not configured. "
            "Set this environment variable to a valid Fernet key."
        )
    return Fernet(key.encode() if isinstance(key, str) else key)


def encrypt_token(plain: str) -> str:
    f = _get_fernet()
    return f.encrypt(plain.encode()).decode()


def decrypt_token(ciphertext: str) -> str:
    f = _get_fernet()
    return f.decrypt(ciphertext.encode()).decode()


def _get_fernet_for_key(key: str) -> Fernet:
    if not key:
        raise TokenEncryptionError(
            "Encryption key is not configured. "
            "Set the appropriate environment variable to a valid Fernet key."
        )
    return Fernet(key.encode() if isinstance(key, str) else key)


def encrypt_with_key(plain: str, key: str) -> str:
    f = _get_fernet_for_key(key)
    return f.encrypt(plain.encode()).decode()


def decrypt_with_key(ciphertext: str, key: str) -> str:
    f = _get_fernet_for_key(key)
    return f.decrypt(ciphertext.encode()).decode()
