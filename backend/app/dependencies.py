from fastapi import Depends, Header, HTTPException, status
import jwt

from .auth_utils import decode_token
from .config import get_settings
from .supabase_client import get_admin_client


def get_current_user(authorization: str = Header(default="", alias="Authorization")) -> dict:
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")

    token = authorization.replace("Bearer ", "", 1).strip()

    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")

    try:
        payload = decode_token(token)
    except jwt.ExpiredSignatureError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired") from exc
    except jwt.InvalidTokenError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token") from exc

    if payload.get("type") != "access":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type")

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    settings = get_settings()
    admin = get_admin_client()

    response = (
        admin.table(settings.supabase_users_table)
        .select("id,phone,role,email,full_name,demo_mode_enabled")
        .eq("id", user_id)
        .limit(1)
        .execute()
    )

    rows = response.data or []
    if not rows:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    user = rows[0]

    return {
        "id": user["id"],
        "phone": user.get("phone", ""),
        "role": user.get("role", "user"),
        "email": user.get("email"),
        "full_name": user.get("full_name", ""),
        "demo_mode_enabled": bool(user.get("demo_mode_enabled", False)),
    }


def require_current_user(user: dict = Depends(get_current_user)) -> dict:
    return user


def require_admin_user(user: dict = Depends(get_current_user)) -> dict:
    settings = get_settings()
    admin = get_admin_client()

    response = (
        admin.table(settings.supabase_users_table)
        .select("id,phone,role,email,full_name")
        .eq("id", user["id"])
        .limit(1)
        .execute()
    )

    rows = response.data or []
    if not rows:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    db_user = rows[0]
    if db_user.get("role", "user") != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")

    return {
        "id": db_user["id"],
        "phone": db_user.get("phone", ""),
        "role": db_user.get("role", "user"),
        "email": db_user.get("email"),
        "full_name": db_user.get("full_name", "")
    }
