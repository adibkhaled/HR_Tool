from __future__ import annotations

import hashlib
import hmac
import secrets
import string
from datetime import datetime, timedelta, timezone
from enum import Enum

import jwt
from passlib.context import CryptContext

from backend.app.core.config import get_settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class UserRole(str, Enum):
    HR_ADMIN = "HR Admin"
    RECRUITER = "Recruiter"
    VIEWER = "Viewer"


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return pwd_context.verify(password, password_hash)


def create_access_token(subject: str, role: UserRole, *, expires_in_minutes: int = 60) -> str:
    settings = get_settings()
    issued_at = datetime.now(timezone.utc)
    payload = {
        "sub": subject,
        "role": role.value,
        "iat": int(issued_at.timestamp()),
        "exp": int((issued_at + timedelta(minutes=expires_in_minutes)).timestamp()),
        "iss": "hr-tool",
    }
    return jwt.encode(payload, settings.jwt_secret.get_secret_value(), algorithm="HS256")


def verify_token(token: str) -> dict:
    settings = get_settings()
    return jwt.decode(token, settings.jwt_secret.get_secret_value(), algorithms=["HS256"], issuer="hr-tool")


def require_roles(allowed: set[UserRole], claims: dict) -> None:
    current_role = claims.get("role")
    if current_role is None:
        raise PermissionError("Missing role claim")

    normalized = UserRole(current_role)
    if normalized not in allowed:
        required = ", ".join(sorted(role.value for role in allowed))
        raise PermissionError(f"This action requires {required} role")


def hash_refresh_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def create_refresh_token() -> str:
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(64))


def is_refresh_token_valid(stored_hash: str, provided_token: str) -> bool:
    return hmac.compare_digest(hash_refresh_token(provided_token), stored_hash)
