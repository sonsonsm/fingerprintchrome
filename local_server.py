#!/usr/bin/env python3
"""Local license and binary distribution server for fingerprintchrome.

Serves:
  - Chromium binary downloads for Linux and Windows
  - Signed SHA256SUMS manifest
  - Local license session API endpoints

Seat model:
  - DEMO-KEY          -> 1 concurrent session (built-in)
  - fp1.<claims>.<sig> -> seats from issuer-minted key (replace only this)

Signing keys (split on purpose):
  - session_priv.hex  -> lease tokens (must match the Pro binary)
  - license_pub.hex   -> verify multi-seat fp1 keys (issuer priv is NOT shipped)
"""
from __future__ import annotations

import hashlib
import json
import sys
import threading
import time
import uuid
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

# Windows embed Python：._pth 隔离模式下 sys.path 常不含脚本目录，PYTHONPATH 也被忽略。
_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

from license_util import DEMO_KEY, b64url_encode, load_priv_hex, load_pub_hex, resolve_license

PORT = 19200
ROOT = Path(__file__).resolve().parent
ARCHIVES_DIR = ROOT / "archives"
# FingerprintChrome LicenseRuntime aborts (SIGABRT) when
#   Now() - lease_start_time_ >= lease_ttl_
# and successful *heartbeat* responses do NOT refresh lease_start_time_
# (only /session/start stores it). A 900s TTL therefore kills the browser
# on the first heartbeat after ~15 minutes even though heartbeats 200 OK.
# Keep this >= max expected headed session length.
LEASE_TTL_SECONDS = 86400
HEARTBEAT_INTERVAL_SECONDS = 300
# Token expires_at is a second hard stop (exit 76 path). Keep in sync with TTL.
TOKEN_TTL_SECONDS = LEASE_TTL_SECONDS

# Lease tokens must be signed with the key embedded in the Pro binary.
SESSION_PRIV_HEX = load_priv_hex(ROOT / "session_priv.hex")
# Multi-seat fp1 keys: verify only (issuer keeps license_priv.hex offline).
LICENSE_PUB_HEX = load_pub_hex(ROOT / "license_pub.hex")

# lease_id -> {key_hash, expires_at, plan, seats, started_at, last_heartbeat_at, heartbeat_count}
_SESSIONS: dict[str, dict] = {}
_SESSIONS_LOCK = threading.Lock()
_LEASE_EVENTS = ROOT / "lease_events.jsonl"


def _lease_log(event: str, **extra) -> None:
    row = {"at": datetime.now(timezone.utc).isoformat(), "event": event, **extra}
    try:
        with _LEASE_EVENTS.open("a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    except Exception:
        pass
    print(f"[license] {event} {json.dumps(extra, ensure_ascii=False)}", flush=True)


def _archive(name: str) -> Path:
    p = ARCHIVES_DIR / name
    if p.is_file():
        return p
    return ROOT / name


ARCHIVES = {
    "linux-x64": _archive("fingerprintchrome-linux-x64.tar.gz"),
    "windows-x64": _archive("fingerprintchrome-windows-x64.zip"),
    "win32-x64": _archive("fingerprintchrome-windows-x64.zip"),
}
MANIFEST = _archive("SHA256SUMS")
SIG = _archive("SHA256SUMS.sig")


def _manifest_versions() -> dict[str, str]:
    """Read linux/windows versions from archives/SHA256SUMS."""
    out: dict[str, str] = {}
    try:
        for line in MANIFEST.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line.startswith("version="):
                out["linux-x64"] = line.split("=", 1)[1].strip() or "latest"
                out.setdefault("linux-arm64", out["linux-x64"])
            m = None
            if line.startswith("#"):
                # # windows-x64=x.y.z
                body = line.lstrip("#").strip()
                if "=" in body:
                    k, v = body.split("=", 1)
                    k, v = k.strip().lower(), v.strip()
                    if k in ("windows-x64", "win32-x64", "linux-x64", "linux-arm64") and v:
                        out[k] = v
                        if k == "windows-x64":
                            out["win32-x64"] = v
    except Exception:
        pass
    if "linux-x64" in out and "windows-x64" not in out:
        out["windows-x64"] = out["linux-x64"]
        out["win32-x64"] = out["linux-x64"]
    return out


def _manifest_version(platform: str | None = None) -> str:
    """Single source of truth for served Chromium version (archives/SHA256SUMS)."""
    versions = _manifest_versions()
    if not versions:
        return "latest"
    plat = (platform or "linux-x64").lower()
    if plat == "win32-x64":
        plat = "windows-x64"
    return versions.get(plat) or versions.get("linux-x64") or next(iter(versions.values()), "latest")



def _key_hash(license_key: str) -> str:
    return hashlib.sha256(license_key.encode("utf-8")).hexdigest()


def _purge_expired(now: float | None = None) -> None:
    now = time.time() if now is None else now
    dead = [lid for lid, s in _SESSIONS.items() if s["expires_at"] <= now]
    for lid in dead:
        sess = _SESSIONS.pop(lid, None) or {}
        _lease_log(
            "lease_expired",
            lease_id=lid,
            ttl_seconds=LEASE_TTL_SECONDS,
            heartbeat_interval_seconds=HEARTBEAT_INTERVAL_SECONDS,
            last_heartbeat_at=sess.get("last_heartbeat_at"),
            heartbeat_count=sess.get("heartbeat_count", 0),
        )


def _active_for_key(key_hash: str, now: float | None = None) -> int:
    now = time.time() if now is None else now
    _purge_expired(now)
    return sum(1 for s in _SESSIONS.values() if s["key_hash"] == key_hash and s["expires_at"] > now)


def _resolve_req(req: dict) -> tuple[dict | None, dict | None]:
    """Returns (info, error_body). info has valid/seats/plan/expires."""
    key = str(req.get("license_key") or "").strip()
    info = resolve_license(key, LICENSE_PUB_HEX)
    if not info["valid"]:
        err = info.get("error") or "invalid_key"
        return None, {"valid": False, "error": err}
    return info, None


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        with (ROOT / "local_server.log").open("a", encoding="utf-8") as f:
            f.write(fmt % args + "\n")
            f.flush()

    def _read(self):
        n = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(n) if n else b""
        try:
            return raw, json.loads(raw.decode()) if raw else {}
        except Exception:
            return raw, {}

    def _send(self, code, obj=None, content_type="application/json"):
        if isinstance(obj, bytes):
            body = obj
        elif obj is None:
            body = b""
        else:
            body = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        if body:
            self.wfile.write(body)

    def _archive_for_request(self):
        p = self.path
        if "linux-x64" in p and p.endswith(".tar.gz"):
            return ARCHIVES["linux-x64"], "application/gzip"
        if ("win32-x64" in p or "windows-x64" in p) and p.endswith(".zip"):
            return ARCHIVES["windows-x64"], "application/zip"
        platform = self.headers.get("X-Platform", "linux-x64").lower()
        return ARCHIVES.get(platform, ARCHIVES["linux-x64"]), "application/octet-stream"

    def _sign_license_token(self, req, info: dict, lease_id: str):
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

        priv = Ed25519PrivateKey.from_private_bytes(bytes.fromhex(SESSION_PRIV_HEX))
        payload = {
            "expires_at": datetime.fromtimestamp(
                time.time() + TOKEN_TTL_SECONDS, tz=timezone.utc
            ).isoformat(),
            "install_id": req.get("install_id", str(uuid.uuid4())),
            "instance_id": req.get("instance_id", str(uuid.uuid4())),
            "issued_at": datetime.now(timezone.utc).isoformat(),
            "lease_id": lease_id,
            "license_key_hash": _key_hash(str(req.get("license_key") or "")),
            "plan": info["plan"],
            "platform": req.get("platform", "linux-x64"),
            "version": req.get("version") or _manifest_version(str(req.get("platform") or "linux-x64")),
            "seats": info["seats"],
        }
        raw = json.dumps(payload, separators=(",", ":")).encode()
        return f"{b64url_encode(raw)}.{b64url_encode(priv.sign(raw))}"

    def do_GET(self):
        p = self.path
        if p.startswith("/api/download/version"):
            from urllib.parse import urlparse, parse_qs
            qs = parse_qs(urlparse(p).query)
            plat = (qs.get("platform") or [None])[0] or self.headers.get("X-Platform") or "linux-x64"
            self._send(200, {
                "version": _manifest_version(plat),
                "platform": plat,
                "requested_channel": "stable",
                "resolved_channel": "stable",
                "fallback": False,
            })
            return
        if p.startswith("/api/download/"):
            archive, ct = self._archive_for_request()
            self._send(200, archive.read_bytes(), ct)
            return
        if p.endswith("/SHA256SUMS"):
            self._send(200, MANIFEST.read_bytes(), "text/plain")
            return
        if p.endswith("/SHA256SUMS.sig"):
            self._send(200, SIG.read_bytes(), "text/plain")
            return
        if p.endswith("/api/license/session/leases"):
            now = time.time()
            with _SESSIONS_LOCK:
                _purge_expired(now)
                leases = []
                for lid, s in _SESSIONS.items():
                    leases.append({
                        "lease_id": lid,
                        "expires_in_seconds": max(0, int(s["expires_at"] - now)),
                        "ttl_seconds": LEASE_TTL_SECONDS,
                        "heartbeat_interval_seconds": HEARTBEAT_INTERVAL_SECONDS,
                        "heartbeat_count": int(s.get("heartbeat_count") or 0),
                        "age_seconds": int(now - float(s.get("started_at") or now)),
                        "last_heartbeat_age_seconds": int(
                            now - float(s.get("last_heartbeat_at") or now)
                        ),
                    })
            self._send(200, {
                "ok": True,
                "active": len(leases),
                "lease_ttl_seconds": LEASE_TTL_SECONDS,
                "heartbeat_interval_seconds": HEARTBEAT_INTERVAL_SECONDS,
                "leases": leases,
            })
            return
        self._send(404, {"detail": "not found"})

    def do_POST(self):
        _raw, req = self._read()
        p = self.path

        if p.endswith("/api/license/validate"):
            info, err = _resolve_req(req)
            if err:
                self._send(403, err)
                return
            self._send(200, {
                "valid": True,
                "plan": info["plan"],
                "expires": info["expires"],
                "seats": info["seats"],
            })
            return

        if p.endswith("/api/license/session/count"):
            info, err = _resolve_req(req)
            if err:
                self._send(403, err)
                return
            kh = _key_hash(str(req.get("license_key") or ""))
            with _SESSIONS_LOCK:
                active = _active_for_key(kh)
            self._send(200, {
                "valid": True,
                "active": active,
                "limit": info["seats"],
            })
            return

        if p.endswith("/api/license/session/start"):
            info, err = _resolve_req(req)
            if err:
                self._send(403, err)
                return
            key = str(req.get("license_key") or "")
            kh = _key_hash(key)
            now = time.time()
            with _SESSIONS_LOCK:
                active = _active_for_key(kh, now)
                if active >= info["seats"]:
                    self._send(403, {
                        "valid": False,
                        "error": "session_limit",
                        "active": active,
                        "limit": info["seats"],
                    })
                    return
                lease_id = f"lease_fp_{int(now * 1000)}_{uuid.uuid4().hex[:8]}"
                _SESSIONS[lease_id] = {
                    "key_hash": kh,
                    "expires_at": now + LEASE_TTL_SECONDS,
                    "plan": info["plan"],
                    "seats": info["seats"],
                    "started_at": now,
                    "last_heartbeat_at": now,
                    "heartbeat_count": 0,
                }
            _lease_log(
                "lease_start",
                lease_id=lease_id,
                ttl_seconds=LEASE_TTL_SECONDS,
                heartbeat_interval_seconds=HEARTBEAT_INTERVAL_SECONDS,
            )
            self._send(200, {
                "valid": True,
                "lease_id": lease_id,
                "heartbeat_interval_seconds": HEARTBEAT_INTERVAL_SECONDS,
                "lease_ttl_seconds": LEASE_TTL_SECONDS,
                "plan": info["plan"],
                "limit": info["seats"],
                "token": self._sign_license_token(req, info, lease_id),
            })
            return

        if p.endswith("/api/license/session/heartbeat"):
            lease_id = str(req.get("lease_id") or "")
            with _SESSIONS_LOCK:
                _purge_expired()
                sess = _SESSIONS.get(lease_id)
                if not sess:
                    self._send(404, {"valid": False, "error": "unknown_lease"})
                    return
                now = time.time()
                sess["expires_at"] = now + LEASE_TTL_SECONDS
                sess["last_heartbeat_at"] = now
                sess["heartbeat_count"] = int(sess.get("heartbeat_count") or 0) + 1
                hb_n = sess["heartbeat_count"]
            _lease_log("lease_heartbeat", lease_id=lease_id, heartbeat_count=hb_n)
            # Include TTL fields for clients that re-apply lease_start on heartbeat.
            # Current Pro 152 still only refreshes lease_start on /start, so start TTL
            # must remain long; these fields are harmless and forward-compatible.
            self._send(200, {
                "valid": True,
                "ok": True,
                "heartbeat_count": hb_n,
                "heartbeat_interval_seconds": HEARTBEAT_INTERVAL_SECONDS,
                "lease_ttl_seconds": LEASE_TTL_SECONDS,
            })
            return

        if p.endswith("/api/license/session/end"):
            lease_id = str(req.get("lease_id") or "")
            with _SESSIONS_LOCK:
                _SESSIONS.pop(lease_id, None)
            _lease_log("lease_end", lease_id=lease_id)
            self._send(200, {"ok": True})
            return

        self._send(404, {"detail": "not found"})


if __name__ == "__main__":
    _lease_log("license_server_start", port=PORT, ttl_seconds=LEASE_TTL_SECONDS)
    # Bind all interfaces so Windows hosts / sibling containers can reach us.
    print(f"Serving on http://0.0.0.0:{PORT}", flush=True)
    print(f"Default seat key: {DEMO_KEY} (1 seat). Replace FINGERPRINTCHROME_LICENSE_KEY for multi-seat.", flush=True)
    HTTPServer(("0.0.0.0", PORT), Handler).serve_forever()
