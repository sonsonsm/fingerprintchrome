#!/usr/bin/env python3
"""Localize CloakBrowser Pro binaries for FingerprintChrome.

1) Session-verify pubkey: after /api/license/session/start\\0 embed our session_pub.hex
   (must match local_server session_priv).

2) User-visible brand: CloakBrowser → FPrintChrome (same length; Chromium string slots
   cannot hold full \"FingerprintChrome\"). Leaves CLOAKBROWSER_* env names and
   cloakbrowser.dev alone so license env wiring keeps working.

Usage:
  ./scripts/localize-session-key.py path/to/chrome
  ./scripts/localize-session-key.py path/to/chrome.dll
  ./scripts/localize-session-key.py --archives
"""
from __future__ import annotations

import argparse
import io
import tarfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MARKER = b"/api/license/session/start\x00"
KEY_LEN = 32

# Equal-length only (Chromium embeds / data-pack strings are fixed-width slots).
BRAND_REPLACEMENTS: list[tuple[bytes, bytes]] = [
    (b"CloakBrowser", b"FPrintChrome"),
]


def load_session_pub(path: Path | None = None) -> bytes:
    p = path or (ROOT / "session_pub.hex")
    raw = p.read_text(encoding="utf-8").strip().splitlines()[-1].strip()
    key = bytes.fromhex(raw)
    if len(key) != KEY_LEN:
        raise SystemExit(f"session_pub must be {KEY_LEN} bytes, got {len(key)} from {p}")
    return key


def patch_session_key(data: bytes, new_key: bytes, *, label: str) -> tuple[bytes, list[str]]:
    notes: list[str] = []
    idx = data.find(MARKER)
    if idx < 0:
        return data, notes
    if data.find(MARKER, idx + 1) >= 0:
        raise SystemExit(f"{label}: session marker appears more than once; refusing to patch")
    off = idx + len(MARKER)
    old = data[off : off + KEY_LEN]
    if len(old) != KEY_LEN:
        raise SystemExit(f"{label}: truncated key at offset {off}")
    if old == new_key:
        notes.append("key: already localized")
        return data, notes
    out = bytearray(data)
    out[off : off + KEY_LEN] = new_key
    notes.append(f"key: {old.hex()} -> {new_key.hex()} @{off}")
    return bytes(out), notes


def patch_brand(data: bytes) -> tuple[bytes, list[str]]:
    notes: list[str] = []
    out = data
    for old, new in BRAND_REPLACEMENTS:
        if len(old) != len(new):
            raise SystemExit(f"brand map length mismatch {old!r} vs {new!r}")
        count = out.count(old)
        if not count:
            continue
        out = out.replace(old, new)
        notes.append(f"brand: {old.decode()}->{new.decode()} x{count}")
    return out, notes


def patch_bytes(data: bytes, new_key: bytes | None, *, label: str, brand: bool) -> tuple[bytes, str]:
    notes: list[str] = []
    cur = data
    if new_key is not None and MARKER in cur:
        cur, n = patch_session_key(cur, new_key, label=label)
        notes.extend(n)
    if brand:
        cur, n = patch_brand(cur)
        notes.extend(n)
    if cur == data:
        return data, f"{label}: no changes" if not notes else f"{label}: {'; '.join(notes)}"
    return cur, f"{label}: {'; '.join(notes) if notes else 'patched'}"


def patch_file(path: Path, new_key: bytes | None, *, brand: bool) -> str:
    data = path.read_bytes()
    patched, msg = patch_bytes(data, new_key, label=str(path), brand=brand)
    if patched == data:
        return msg
    tmp = path.with_suffix(path.suffix + ".localize-tmp")
    tmp.write_bytes(patched)
    tmp.chmod(path.stat().st_mode)
    tmp.replace(path)
    return msg


def _should_patch_member(name: str) -> bool:
    base = Path(name).name.lower()
    if base in ("chrome", "chrome.exe", "chrome.dll"):
        return True
    return base.endswith(".pak")


def patch_linux_archive(archive: Path, new_key: bytes, *, brand: bool) -> list[str]:
    msgs: list[str] = []
    with tarfile.open(archive, "r:gz") as src_tf:
        members = src_tf.getmembers()
        chrome_cands = [m for m in members if m.isfile() and Path(m.name).name == "chrome"]
        if not chrome_cands:
            raise SystemExit(f"{archive}: chrome binary not found")
        patch_names = [m.name for m in members if m.isfile() and _should_patch_member(m.name)]
        if not patch_names:
            raise SystemExit(f"{archive}: nothing to patch")

        # Read all file payloads we may rewrite or copy
        file_payloads: dict[str, bytes] = {}
        patched_payloads: dict[str, bytes] = {}
        for m in members:
            if not m.isfile():
                continue
            f = src_tf.extractfile(m)
            if f is None:
                continue
            raw = f.read()
            file_payloads[m.name] = raw
            if m.name not in patch_names:
                continue
            key = new_key if Path(m.name).name == "chrome" else None
            new_data, msg = patch_bytes(raw, key, label=f"{archive.name}:{m.name}", brand=brand)
            msgs.append(msg)
            if new_data != raw:
                patched_payloads[m.name] = new_data

        if not patched_payloads:
            return msgs

        out = archive.with_suffix(archive.suffix + ".localize-tmp")
        with tarfile.open(out, "w:gz") as out_tf:
            for m in members:
                if m.isfile():
                    payload = patched_payloads.get(m.name, file_payloads[m.name])
                    info = tarfile.TarInfo(name=m.name)
                    info.size = len(payload)
                    info.mode = m.mode
                    info.mtime = m.mtime
                    info.uid = m.uid
                    info.gid = m.gid
                    info.uname = m.uname
                    info.gname = m.gname
                    out_tf.addfile(info, io.BytesIO(payload))
                else:
                    out_tf.addfile(m)
        out.replace(archive)
    return msgs


def patch_windows_archive(archive: Path, new_key: bytes, *, brand: bool) -> list[str]:
    msgs: list[str] = []
    with zipfile.ZipFile(archive, "r") as zf:
        names = [n for n in zf.namelist() if _should_patch_member(n)]
        if not any(Path(n).name.lower() == "chrome.dll" for n in names):
            raise SystemExit(f"{archive}: chrome.dll not found")
        patched_payloads: dict[str, bytes] = {}
        for name in names:
            raw = zf.read(name)
            key = new_key if Path(name).name.lower() == "chrome.dll" else None
            new_data, msg = patch_bytes(raw, key, label=f"{archive.name}:{name}", brand=brand)
            msgs.append(msg)
            if new_data != raw:
                patched_payloads[name] = new_data
        if not patched_payloads:
            return msgs
        out = archive.with_suffix(archive.suffix + ".localize-tmp")
        with zipfile.ZipFile(out, "w") as out_zf:
            for info in zf.infolist():
                payload = patched_payloads.get(info.filename) or zf.read(info.filename)
                new_info = zipfile.ZipInfo(filename=info.filename, date_time=info.date_time)
                new_info.compress_type = info.compress_type
                new_info.external_attr = info.external_attr
                new_info.create_system = info.create_system
                new_info.flag_bits = info.flag_bits
                out_zf.writestr(new_info, payload)
        out.replace(archive)
    return msgs


def patch_archives(new_key: bytes, *, brand: bool) -> list[str]:
    arch = ROOT / "archives"
    msgs: list[str] = []
    linux = arch / "fingerprintchrome-linux-x64.tar.gz"
    windows = arch / "fingerprintchrome-windows-x64.zip"
    if not linux.is_file() or not windows.is_file():
        raise SystemExit(f"missing archives under {arch}")
    msgs.extend(patch_linux_archive(linux, new_key, brand=brand))
    msgs.extend(patch_windows_archive(windows, new_key, brand=brand))
    return msgs


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("paths", nargs="*", type=Path, help="chrome / chrome.dll / .pak paths")
    ap.add_argument("--archives", action="store_true", help="patch archives/ linux+windows packages")
    ap.add_argument("--pub", type=Path, default=None, help="override session_pub.hex path")
    ap.add_argument("--no-brand", action="store_true", help="only patch session key")
    ap.add_argument("--brand-only", action="store_true", help="only patch CloakBrowser→FPrintChrome")
    args = ap.parse_args()
    if not args.paths and not args.archives:
        ap.error("provide binary paths and/or --archives")
    brand = not args.no_brand
    if args.brand_only and args.no_brand:
        ap.error("--brand-only and --no-brand conflict")
    new_key: bytes | None
    if args.brand_only:
        new_key = None
    else:
        new_key = load_session_pub(args.pub)
    for p in args.paths:
        key = None if (args.brand_only or p.suffix.lower() == ".pak") else new_key
        print(patch_file(p, key, brand=brand))
    if args.archives:
        if new_key is None:
            # brand-only archives: still load key so chrome/dll stay licensed
            new_key = load_session_pub(args.pub)
            for msg in patch_archives(new_key, brand=True):
                print(msg)
        else:
            for msg in patch_archives(new_key, brand=brand):
                print(msg)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
