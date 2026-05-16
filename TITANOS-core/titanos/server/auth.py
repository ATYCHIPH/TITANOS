import os
import time
import warnings
import base64
import hashlib
import hmac
import json
from typing import Optional, Dict, Any
from fastapi import HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

try:
    from jose import jwt, JWTError
except ImportError:
    jwt = None

    class JWTError(Exception):
        pass

from ..config.settings import settings


SECRET_KEY = settings.JWT_SECRET
if SECRET_KEY == "super-secret-dev-key":
    if settings.ENVIRONMENT.lower() in {"prod", "production"}:
        raise RuntimeError("JWT_SECRET must be configured in production.")
    warnings.warn(
        "Using development JWT secret. Set JWT_SECRET for shared or production use.",
        RuntimeWarning,
        stacklevel=2,
    )
ALGORITHM = "HS256"

security = HTTPBearer()

def create_access_token(data: dict, expires_delta_seconds: Optional[int] = 3600) -> str:
    """Create a new JWT access token."""
    to_encode = data.copy()
    expire = time.time() + expires_delta_seconds
    to_encode.update({"exp": expire})
    if jwt is not None:
        return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return _encode_dev_token(to_encode)

def decode_access_token(token: str) -> Dict[str, Any]:
    """Decode and verify a JWT access token."""
    try:
        if jwt is not None:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        else:
            payload = _decode_dev_token(token)
        if payload.get("exp", 0) < time.time():
            raise JWTError("expired token")
        return payload
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

def get_current_user(credentials: HTTPAuthorizationCredentials = Security(security)) -> Dict[str, Any]:
    """Dependency to get the current user from the JWT token."""
    token = credentials.credentials
    return decode_access_token(token)


def _encode_dev_token(payload: dict) -> str:
    header = {"alg": "HS256", "typ": "JWT"}
    parts = [_b64_json(header), _b64_json(payload)]
    signing_input = ".".join(parts).encode("ascii")
    signature = hmac.new(
        SECRET_KEY.encode("utf-8"), signing_input, hashlib.sha256
    ).digest()
    return ".".join([*parts, _b64(signature)])


def _decode_dev_token(token: str) -> Dict[str, Any]:
    try:
        header, payload, signature = token.split(".")
    except ValueError as exc:
        raise JWTError("malformed token") from exc
    signing_input = f"{header}.{payload}".encode("ascii")
    expected = hmac.new(
        SECRET_KEY.encode("utf-8"), signing_input, hashlib.sha256
    ).digest()
    if not hmac.compare_digest(_b64(expected), signature):
        raise JWTError("invalid signature")
    return json.loads(_b64_decode(payload))


def _b64_json(data: dict) -> str:
    return _b64(json.dumps(data, separators=(",", ":")).encode("utf-8"))


def _b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _b64_decode(data: str) -> str:
    padding = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(data + padding).decode("utf-8")
