import base64
import hashlib
import hmac
import json
import secrets
from datetime import datetime, timedelta

from app.config import SECRET_KEY


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.sha256(f"{salt}:{password}".encode("utf-8")).hexdigest()
    return f"{salt}${digest}"


def verify_password(password: str, password_hash: str) -> bool:
    try:
        salt, digest = password_hash.split("$", 1)
    except ValueError:
        return False
    expected = hashlib.sha256(f"{salt}:{password}".encode("utf-8")).hexdigest()
    return hmac.compare_digest(expected, digest)


def _b64_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("utf-8").rstrip("=")


def _b64_decode(data: str) -> bytes:
    padding = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(data + padding)


def create_token(user_id: int, username: str, hours: int = 24) -> str:
    payload = {
        "user_id": user_id,
        "username": username,
        "exp": (datetime.utcnow() + timedelta(hours=hours)).isoformat(),
    }
    payload_part = _b64_encode(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
    signature = hmac.new(SECRET_KEY.encode("utf-8"), payload_part.encode("utf-8"), hashlib.sha256).digest()
    return f"{payload_part}.{_b64_encode(signature)}"


def decode_token(token: str) -> dict:
    payload_part, signature_part = token.split(".", 1)
    expected = hmac.new(SECRET_KEY.encode("utf-8"), payload_part.encode("utf-8"), hashlib.sha256).digest()
    actual = _b64_decode(signature_part)
    if not hmac.compare_digest(expected, actual):
        raise ValueError("invalid token signature")
    payload = json.loads(_b64_decode(payload_part))
    if datetime.fromisoformat(payload["exp"]) < datetime.utcnow():
        raise ValueError("token expired")
    return payload

