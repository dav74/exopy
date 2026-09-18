import os
import base64
import hashlib
from cryptography.fernet import Fernet

def _derive_fernet_key() -> bytes:
    secret = os.getenv("SECRET_KEY", "")
    digest = hashlib.sha256(f"exopy-llm-api-keys:{secret}".encode()).digest()
    return base64.urlsafe_b64encode(digest)

_fernet = Fernet(_derive_fernet_key())

def encrypt_secret(plain: str) -> str:
    return _fernet.encrypt(plain.encode()).decode()

def decrypt_secret(token: str) -> str | None:
    try:
        return _fernet.decrypt(token.encode()).decode()
    except Exception:
        return None
