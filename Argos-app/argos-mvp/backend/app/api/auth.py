"""
FastAPI auth dependencies — JWT validation + tenant resolution.
All user-facing endpoints depend on get_current_tenant().
"""

import logging
from dataclasses import dataclass
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from app.config import get_settings
from app.services import database as db

logger = logging.getLogger("argos.auth")

_security = HTTPBearer()


@dataclass
class AuthContext:
    user_id: str
    tenant_id: str
    role: str      # "owner" | "employee"
    token: str


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(_security),
) -> dict:
    settings = get_settings()
    token = credentials.credentials
    try:
        payload = jwt.decode(
            token,
            settings.supabase_jwt_secret,
            algorithms=["HS256"],
            audience="authenticated",
        )
        user_id: str = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Token inválido")
        return {"user_id": user_id, "token": token}
    except JWTError:
        raise HTTPException(status_code=401, detail="Token inválido o expirado")


async def get_current_tenant(
    user: dict = Depends(get_current_user),
) -> AuthContext:
    user_tenant = db.get_user_tenant(user["user_id"])
    if not user_tenant:
        logger.warning("User %s has no tenant assignment", user["user_id"])
        raise HTTPException(status_code=403, detail="Usuario sin empresa asignada")

    # Scope all subsequent DB calls in this request to the user's JWT (enables RLS)
    db.set_request_db(user["token"])

    return AuthContext(
        user_id=user["user_id"],
        tenant_id=user_tenant["tenant_id"],
        role=user_tenant["role"],
        token=user["token"],
    )
