#!/usr/bin/env bash
# Ensure linux/windows archives exist under archives/ (local cache; not in git).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
ARCH="$ROOT/archives"
need=(fingerprintchrome-linux-x64.tar.gz fingerprintchrome-windows-x64.zip)
missing=0
for f in "${need[@]}"; do
  if [[ ! -f "$ARCH/$f" ]]; then
    # one-time compat: root leftover
    if [[ -f "$ROOT/$f" ]]; then
      mkdir -p "$ARCH"
      mv "$ROOT/$f" "$ARCH/$f"
      echo "moved $f -> archives/"
      continue
    fi
    echo "missing: $ARCH/$f" >&2
    missing=1
  fi
done
if [[ "$missing" -ne 0 ]]; then
  echo "Place archives under fingerprintchrome/archives/ (gitignored)," >&2
  echo "or run: ./scripts/fetch-archives.sh" >&2
  echo "GitHub: attach them as Release assets — do not commit to main." >&2
  exit 1
fi
echo "archives ok under $ARCH"
