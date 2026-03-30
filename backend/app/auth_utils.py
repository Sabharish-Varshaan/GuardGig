from datetime import datetime, timedelta, timezone

import bcrypt
import jwt

from .config import get_settings


def hash_password(password: str) -> str:
    encoded = password.encode("utf-8")
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(encoded, salt).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))


def create_access_token(user_id: str, phone: str) -> str:
    settings = get_settings()
    now = datetime.now(timezone.utc)

    payload = {
        "sub": user_id,
        "phone": phone,
        "type": "access",
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=settings.access_token_exp_minutes)).timestamp())
    }

    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def create_refresh_token(user_id: str, phone: str) -> str:
    settings = get_settings()
    now = datetime.now(timezone.utc)

    payload = {
        "sub": user_id,
        "phone": phone,
        "type": "refresh",
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(days=settings.refresh_token_exp_days)).timestamp())
    }

    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> dict:
    settings = get_settings()
    return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
