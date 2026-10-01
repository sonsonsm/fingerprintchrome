#!/usr/bin/env bash
# Fetch Chromium archives from GitHub Releases into archives/ (never commits them).
#
# Env:
#   FINGERPRINTCHROME_RELEASE_TAG   e.g. chromium-v152.0.7977.82.2 (optional if SHA256SUMS exists)
#   FINGERPRINTCHROME_RELEASE_REPO  default: from git remote or example/fingerprintchrome
#   FINGERPRINTCHROME_RELEASE_BASE  optional full URL prefix (skips gh)
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
ARCH="$ROOT/archives"
mkdir -p "$ARCH"

if [[ -n "${FINGERPRINTCHROME_RELEASE_TAG:-}" ]]; then
  TAG="$FINGERPRINTCHROME_RELEASE_TAG"
elif [[ -f "$ARCH/SHA256SUMS" ]]; then
  VER="$(sed -n 's/^version=//p' "$ARCH/SHA256SUMS" | head -1)"
  if [[ -z "$VER" ]]; then
    echo "archives/SHA256SUMS missing version= line" >&2
    exit 1
  fi
  TAG="chromium-v${VER}"
else
  echo "Set FINGERPRINTCHROME_RELEASE_TAG=chromium-vX.Y... or place archives/SHA256SUMS" >&2
  exit 1
fi

files=(
  fingerprintchrome-linux-x64.tar.gz
  fingerprintchrome-windows-x64.zip
  SHA256SUMS
  SHA256SUMS.sig
)

have_all=1
for f in "${files[@]}"; do
  if [[ ! -f "$ARCH/$f" ]]; then have_all=0; break; fi
done
if [[ "$have_all" -eq 1 ]]; then
  echo "already present under $ARCH"
  exit 0
fi

download() {
  local url="$1" out="$2"
  echo "GET $url"
  curl -fL --retry 3 --retry-delay 2 --connect-timeout 30 --max-time 900 -o "$out" "$url"
}

if [[ -n "${FINGERPRINTCHROME_RELEASE_BASE:-}" ]]; then
  BASE="${FINGERPRINTCHROME_RELEASE_BASE%/}"
  for f in "${files[@]}"; do
    [[ -f "$ARCH/$f" ]] && continue
    download "$BASE/$f" "$ARCH/$f"
  done
elif command -v gh >/dev/null 2>&1; then
  REPO="${FINGERPRINTCHROME_RELEASE_REPO:-}"
  if [[ -z "$REPO" ]]; then
    REPO="$(git -C "$ROOT" remote get-url origin 2>/dev/null | sed -E 's#.*[:/]([^/]+/[^/]+)(\.git)?$#\1#' || true)"
  fi
  if [[ -z "$REPO" || "$REPO" == *"example/"* ]]; then
    echo "Set FINGERPRINTCHROME_RELEASE_REPO=owner/repo (or FINGERPRINTCHROME_RELEASE_BASE=...)" >&2
    exit 1
  fi
  echo "gh release download $TAG from $REPO -> $ARCH"
  gh release download "$TAG" -R "$REPO" -D "$ARCH" -p 'fingerprintchrome-*' -p 'SHA256SUMS*' --clobber
else
  echo "Need gh CLI or FINGERPRINTCHROME_RELEASE_BASE=https://..." >&2
  exit 1
fi

"$ROOT/scripts/ensure-archives.sh"
