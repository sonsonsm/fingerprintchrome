#!/usr/bin/env bash
# Rewrite archives/SHA256SUMS from current tarball/zip (does not sign; keep .sig private).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
ARCH="$ROOT/archives"
"$ROOT/scripts/ensure-archives.sh"
cd "$ARCH"
{
  sha256sum fingerprintchrome-linux-x64.tar.gz
  sha256sum fingerprintchrome-windows-x64.zip
} > SHA256SUMS
echo "wrote $ARCH/SHA256SUMS"
cat SHA256SUMS
echo "Sign privately to produce SHA256SUMS.sig (do not commit private key)."
