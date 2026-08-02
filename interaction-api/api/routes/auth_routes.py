"""Signup, login, and profile endpoints using signed JWT bearer tokens."""
from __future__ import annotations

import base64
import hashlib
import hmac
import os
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from jose import jwt
from pydantic import BaseModel, Field

from ...config import settings
from ...db.user_repository import UserRepository
from ...integrations.graph_client import GraphClient
from ...utils.exceptions import GraphWritebackError
from ..dependencies import get_graph_client, get_user_repository
from ..middleware.auth_middleware import authenticate_request

router = APIRouter(prefix="/auth", tags=["auth"])


class SignupInput(BaseModel):
    login: str = Field(min_length=3, max_length=50, pattern=r"^[A-Za-z0-9_.-]+$")
    email: str = Field(min_length=5, max_length=254, pattern=r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
    display_name: str = Field(min_length=1, max_length=80)
    password: str = Field(min_length=8, max_length=256)


class LoginInput(BaseModel):
    login: str = Field(min_length=1, max_length=50)
    password: str = Field(min_length=1, max_length=256)


def _hash_password(password: str, salt: bytes | None = None) -> str:
    salt = salt or os.urandom(16)
    digest = hashlib.scrypt(password.encode("utf-8"), salt=salt, n=2**14, r=8, p=1)
    return f"scrypt${base64.b64encode(salt).decode()}${base64.b64encode(digest).decode()}"


def _password_matches(password: str, encoded: str) -> bool:
    try:
        _, salt_b64, digest_b64 = encoded.split("$", 2)
        candidate = _hash_password(password, base64.b64decode(salt_b64))
        return hmac.compare_digest(candidate, encoded)
    except (ValueError, TypeError):
        return False


def _profile(user: dict) -> dict:
    return {
        "id": str(user["id"]), "login": user["login"], "email": user["email"],
        "displayName": user["display_name"],
        "createdAt": user["created_at"].isoformat() if user.get("created_at") else None,
        "lastLoginAt": user["last_login_at"].isoformat() if user.get("last_login_at") else None,
    }


def _token(user_id: str) -> str:
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_expire_minutes)
    return jwt.encode({"sub": user_id, "exp": expires_at}, settings.jwt_secret, algorithm=settings.jwt_algorithm)


@router.post("/signup", status_code=status.HTTP_201_CREATED)
async def signup(payload: SignupInput, users: UserRepository = Depends(get_user_repository), graph: GraphClient = Depends(get_graph_client)):
    login, email = payload.login.lower(), str(payload.email).lower()
    if await users.get_by_login(login):
        raise HTTPException(status_code=409, detail="That login is already in use")
    user_id = str(uuid4())
    try:
        user = await users.create(user_id=user_id, login=login, email=email, display_name=payload.display_name.strip(), password_hash=_hash_password(payload.password))
    except Exception as exc:
        if "unique" in str(exc).lower():
            raise HTTPException(status_code=409, detail="That login or email is already in use") from exc
        raise HTTPException(status_code=503, detail="Unable to create account") from exc
    try:
        await graph.upsert_account(user_id=user_id, login=login, email=email, display_name=user["display_name"])
    except GraphWritebackError as exc:
        await users.delete(user_id)
        raise HTTPException(status_code=503, detail="Unable to sync the account to Neo4j; no account was created") from exc
    return {"token": _token(user_id), "user": _profile(user)}


@router.post("/login")
async def login(payload: LoginInput, users: UserRepository = Depends(get_user_repository), graph: GraphClient = Depends(get_graph_client)):
    user = await users.get_by_login(payload.login.lower())
    if not user or not _password_matches(payload.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid login or password")
    user = await users.mark_logged_in(str(user["id"]))
    try:
        await graph.upsert_account(user_id=str(user["id"]), login=user["login"], email=user["email"], display_name=user["display_name"])
    except GraphWritebackError as exc:
        raise HTTPException(status_code=503, detail="Unable to sync login to Neo4j") from exc
    return {"token": _token(str(user["id"])), "user": _profile(user)}


@router.get("/me")
async def me(user_id: str = Depends(authenticate_request), users: UserRepository = Depends(get_user_repository)):
    user = await users.get_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {"user": _profile(user)}
