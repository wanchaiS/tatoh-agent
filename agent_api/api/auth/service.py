from datetime import datetime, timedelta, timezone

import bcrypt
import jwt

from core.config import settings


def _load_users() -> dict[str, str]:
    """Load admin users from settings — fails fast if none configured."""
    users = settings.admin_users
    if not users:
        raise RuntimeError(
            "No admin users configured. Set ADMIN_USER_<NAME>=<bcrypt_hash> env vars."
        )
    return users


# Load once at import time — fail fast on startup if misconfigured.
_users: dict[str, str] = _load_users()


def verify_credentials(username: str, password: str) -> bool:
    """Return True if username exists and password matches stored bcrypt hash."""
    stored_hash = _users.get(username.lower())
    if not stored_hash:
        return False
    return bcrypt.checkpw(password.encode(), stored_hash.encode())


def create_token(username: str) -> str:
    """Sign and return a JWT for the given username."""
    payload = {
        "sub": username,
        "exp": datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_expire_minutes),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> str | None:
    """Decode token and return username, or None if invalid/expired."""
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        return payload.get("sub")
    except jwt.InvalidTokenError:
        return None
