import base64
import hashlib
import hmac
import json
import secrets
import time
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.config import SECRET_KEY, TOKEN_EXPIRE_HOURS
from app.database import get_db
from app.models import User


security = HTTPBearer(auto_error=False)
PBKDF2_ITERATIONS = 260000


def _b64_encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).decode("ascii").rstrip("=")


def _b64_decode(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), PBKDF2_ITERATIONS)
    return f"pbkdf2${PBKDF2_ITERATIONS}${salt}${digest.hex()}"


def _verify_legacy_password(password: str, password_hash: str) -> bool:
    try:
        salt, digest = password_hash.split("$", 1)
    except ValueError:
        return False
    expected = hashlib.sha256(f"{salt}:{password}".encode("utf-8")).hexdigest()
    return hmac.compare_digest(expected, digest)


def verify_password(password: str, password_hash: str) -> bool:
    if not password_hash.startswith("pbkdf2$"):
        return _verify_legacy_password(password, password_hash)
    try:
        _, iterations, salt, digest = password_hash.split("$", 3)
        expected = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), int(iterations)).hex()
    except (ValueError, TypeError):
        return False
    return hmac.compare_digest(expected, digest)


def create_token(user_id: int, username: str, role: str) -> str:
    now = int(time.time())
    header = {"alg": "HS256", "typ": "JWT"}
    payload = {
        "sub": str(user_id),
        "username": username,
        "role": role,
        "iat": now,
        "exp": now + TOKEN_EXPIRE_HOURS * 3600,
    }
    header_part = _b64_encode(json.dumps(header, separators=(",", ":")).encode("utf-8"))
    payload_part = _b64_encode(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
    signing_input = f"{header_part}.{payload_part}".encode("ascii")
    signature = hmac.new(SECRET_KEY.encode("utf-8"), signing_input, hashlib.sha256).digest()
    return f"{header_part}.{payload_part}.{_b64_encode(signature)}"


def decode_token(token: str) -> dict:
    try:
        header_part, payload_part, signature_part = token.split(".", 2)
        signing_input = f"{header_part}.{payload_part}".encode("ascii")
        expected = hmac.new(SECRET_KEY.encode("utf-8"), signing_input, hashlib.sha256).digest()
        if not hmac.compare_digest(expected, _b64_decode(signature_part)):
            raise ValueError("invalid token signature")
        payload = json.loads(_b64_decode(payload_part))
        if int(payload["exp"]) < int(time.time()):
            raise ValueError("token expired")
        return payload
    except (ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
        raise ValueError("invalid or expired token") from exc


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="请先登录")
    try:
        payload = decode_token(credentials.credentials)
        user_id = int(payload["sub"])
    except (ValueError, KeyError, TypeError) as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="登录已失效") from exc
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="用户不存在")
    return user


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="需要管理员权限")
    return current_user
