"""Shared license key mint / verify helpers for fingerprintchrome.

User-facing key (the only thing customers replace):
  - DEMO-KEY              -> seats=1 (built-in, no signature)
  - fp1.<claims>.<sig>    -> seats from signed claims (issuer mint)

Keys:
  - license_pub.hex   -> shipped; verifies multi-seat fp1 keys
  - license_priv.hex  -> issuer only (.issuer/); never ship / never commit
  - session_*.hex     -> lease tokens for the Pro binary (separate from seat mint)
"""
from __future__ import annotations

import base64
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DEMO_KEY = "DEMO-KEY"
DEMO_SEATS = 1
DEMO_PLAN = "solo"
KEY_PREFIX = "fp1"


def b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def b64url_decode(text: str) -> bytes:
    pad = "=" * (-len(text) % 4)
    return base64.urlsafe_b64decode(text + pad)


def _parse_expires(value: Any) -> datetime | None:
    if value is None or value == "":
        return None
    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(float(value), tz=timezone.utc)
    text = str(value).strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    dt = datetime.fromisoformat(text)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def load_priv_hex(path: Path) -> str:
    raw = path.read_text(encoding="utf-8").strip()
    # Allow example-style comments
    lines = [ln.strip() for ln in raw.splitlines() if ln.strip() and not ln.strip().startswith("#")]
    hex_str = lines[-1] if lines else ""
    if len(hex_str) != 64:
        raise ValueError(f"expected 64 hex chars in {path}, got {len(hex_str)}")
    bytes.fromhex(hex_str)
    return hex_str


def load_pub_hex(path: Path) -> str:
    return load_priv_hex(path)


def mint_license_key(
    *,
    priv_hex: str,
    seats: int,
    plan: str = "team",
    expires: str | None = None,
    kid: str | None = None,
) -> str:
    if seats < 1:
        raise ValueError("seats must be >= 1")
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

    claims: dict[str, Any] = {
        "v": 1,
        "seats": int(seats),
        "plan": plan,
        "iat": datetime.now(timezone.utc).isoformat(),
    }
    if expires:
        # Normalize / validate
        claims["expires"] = _parse_expires(expires).isoformat()
    if kid:
        claims["kid"] = str(kid)

    payload = json.dumps(claims, separators=(",", ":"), sort_keys=True).encode("utf-8")
    priv = Ed25519PrivateKey.from_private_bytes(bytes.fromhex(priv_hex))
    sig = priv.sign(payload)
    return f"{KEY_PREFIX}.{b64url_encode(payload)}.{b64url_encode(sig)}"


def resolve_license(license_key: str, pub_hex: str) -> dict[str, Any]:
    """Return {valid, seats, plan, expires, error?} for a user license key."""
    key = (license_key or "").strip()
    if not key:
        return {"valid": False, "seats": 0, "plan": None, "expires": None, "error": "missing_key"}

    if key == DEMO_KEY:
        return {
            "valid": True,
            "seats": DEMO_SEATS,
            "plan": DEMO_PLAN,
            "expires": None,
            "error": None,
        }

    parts = key.split(".")
    if len(parts) != 3 or parts[0] != KEY_PREFIX:
        return {"valid": False, "seats": 0, "plan": None, "expires": None, "error": "invalid_key"}

    try:
        payload = b64url_decode(parts[1])
        sig = b64url_decode(parts[2])
        claims = json.loads(payload.decode("utf-8"))
    except Exception:
        return {"valid": False, "seats": 0, "plan": None, "expires": None, "error": "malformed_key"}

    try:
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

        pub = Ed25519PublicKey.from_public_bytes(bytes.fromhex(pub_hex))
        pub.verify(sig, payload)
    except Exception:
        return {"valid": False, "seats": 0, "plan": None, "expires": None, "error": "bad_signature"}

    seats = claims.get("seats")
    if not isinstance(seats, int) or seats < 1:
        return {"valid": False, "seats": 0, "plan": None, "expires": None, "error": "bad_seats"}

    expires_raw = claims.get("expires")
    try:
        expires_dt = _parse_expires(expires_raw)
    except Exception:
        return {"valid": False, "seats": 0, "plan": None, "expires": None, "error": "bad_expires"}

    if expires_dt is not None and expires_dt < datetime.now(timezone.utc):
        return {
            "valid": False,
            "seats": seats,
            "plan": str(claims.get("plan") or "team"),
            "expires": expires_dt.isoformat(),
            "error": "expired",
        }

    return {
        "valid": True,
        "seats": seats,
        "plan": str(claims.get("plan") or "team"),
        "expires": expires_dt.isoformat() if expires_dt else None,
        "error": None,
        "kid": claims.get("kid"),
    }
