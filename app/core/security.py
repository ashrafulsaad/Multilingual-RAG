import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone

import jwt

from app.core.config import get_settings


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 120_000)
    return f"{salt}${digest.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        salt, expected = stored.split("$", 1)
        actual = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 120_000).hex()
        return hmac.compare_digest(actual, expected)
    except ValueError:
        return False


def create_access_token(user_id: str, username: str, expires_minutes: int = 60) -> str:
    secret = get_settings().auth_secret
    expires = datetime.now(timezone.utc) + timedelta(minutes=expires_minutes)
    return jwt.encode({"sub": user_id, "username": username, "exp": expires}, secret, algorithm="HS256")


def decode_access_token(token: str) -> dict:
    secret = get_settings().auth_secret
    return jwt.decode(token, secret, algorithms=["HS256"])