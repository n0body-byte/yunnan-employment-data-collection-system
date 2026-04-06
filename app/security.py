from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
import time
from typing import Any

from app.config import settings

PBKDF2_ITERATIONS = 100_000


def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("utf-8")


def _b64url_decode(data: str) -> bytes:
    padding = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(data + padding)


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    password_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        PBKDF2_ITERATIONS,
    )
    return f"pbkdf2_sha256${PBKDF2_ITERATIONS}${_b64url_encode(salt)}${_b64url_encode(password_hash)}"


def verify_password(password: str, password_hash: str) -> bool:
    try:
        algorithm, iterations_str, salt_encoded, hash_encoded = password_hash.split("$", 3)
    except ValueError:
        return False

    if algorithm != "pbkdf2_sha256":
        return False

    iterations = int(iterations_str)
    salt = _b64url_decode(salt_encoded)
    expected_hash = _b64url_decode(hash_encoded)
    actual_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        iterations,
    )
    return hmac.compare_digest(actual_hash, expected_hash)


def create_access_token(subject: str, role: str, region: str) -> str:
    header = {"alg": settings.jwt_algorithm, "typ": "JWT"}
    now = int(time.time())
    payload = {
        "sub": subject,
        "role": role,
        "region": region,
        "iat": now,
        "exp": now + settings.access_token_expire_minutes * 60,
    }

    header_segment = _b64url_encode(json.dumps(header, separators=(",", ":")).encode("utf-8"))
    payload_segment = _b64url_encode(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
    signing_input = f"{header_segment}.{payload_segment}".encode("utf-8")
    signature = hmac.new(
        settings.jwt_secret_key.encode("utf-8"),
        signing_input,
        hashlib.sha256,
    ).digest()
    return f"{header_segment}.{payload_segment}.{_b64url_encode(signature)}"


def decode_access_token(token: str) -> dict[str, Any]:
    try:
        header_segment, payload_segment, signature_segment = token.split(".")
    except ValueError as exc:
        raise ValueError("Invalid JWT format") from exc

    signing_input = f"{header_segment}.{payload_segment}".encode("utf-8")
    expected_signature = hmac.new(
        settings.jwt_secret_key.encode("utf-8"),
        signing_input,
        hashlib.sha256,
    ).digest()
    actual_signature = _b64url_decode(signature_segment)
    if not hmac.compare_digest(expected_signature, actual_signature):
        raise ValueError("Invalid JWT signature")

    header = json.loads(_b64url_decode(header_segment))
    payload = json.loads(_b64url_decode(payload_segment))
    if header.get("alg") != settings.jwt_algorithm:
        raise ValueError("Unsupported JWT algorithm")
    if payload.get("exp") is not None and int(payload["exp"]) < int(time.time()):
        raise ValueError("JWT token has expired")
    return payload
