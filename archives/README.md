# Local binary cache (not in git)

```text
archives/
├── fingerprintchrome-linux-x64.tar.gz
├── fingerprintchrome-windows-x64.zip
├── SHA256SUMS
└── SHA256SUMS.sig
```

**Download (users):**

```bash
FINGERPRINTCHROME_RELEASE_REPO=owner/fingerprintchrome ./scripts/fetch-archives.sh
```

## Remotes (maintainers)

| Remote | What | How |
|--------|------|-----|
| `origin` (Weixin) | Full tree (incl. maintainer scripts) | `git push origin main` |
| `github` (public) | Filtered snapshot | `./scripts/sync-github.sh` |

GitHub excludes issuer tooling / secrets (see `scripts/sync-github.sh`). Private keys stay gitignored (`.issuer/`, `download_priv.hex`).

**Upload packages → GitHub Release** (not `main`):

```bash
export GITHUB_TOKEN=ghp_...
export GITHUB_REPO=owner/fingerprintchrome
./scripts/publish-release.sh
# optional: ./scripts/publish-release.sh chromium-v<version-from-SHA256SUMS>
```

Or push a `chromium-v*` tag with repo secret `ARCHIVE_RELEASE_BASE` (CI pulls from that mirror into the Release).

Do not commit archive binaries to `main`.

## Localize (session key + brand)

Official CloakBrowser embeds its session-verify pubkey after `/api/license/session/start`.
After fetching a new upstream archive, rewrite it to our `session_pub.hex` (matches `session_priv` used by `local_server.py`) and rebrand user-visible strings:

- `CloakBrowser` → `FPrintChrome` (same length; Chromium string slots cannot hold full `FingerprintChrome`)
- Leaves `CLOAKBROWSER_*` env names and `cloakbrowser.dev` alone

```bash
./scripts/localize-session-key.py --archives
# then refresh SHA256SUMS + SHA256SUMS.sig (ed25519 with download_priv.hex)
```

Official (unpatched) copies are kept as `*.bak-official` next to the archives.
