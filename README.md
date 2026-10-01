# fingerprintchrome

[English](README.md) | [简体中文](README.zh-CN.md)

### Stealth Chromium that passes bot detection.

Not a config hack. Not JS injected into the page. Fingerprints are changed inside Chromium and compiled in — sites see a normal Chrome.

- Passes **Cloudflare Turnstile**, **FingerprintJS**, **BrowserScan**, and 30+ other checks
- **reCAPTCHA v3 ~0.9** (human-level)
- Human-like mouse / keyboard / scroll (`humanize: true`)
- Same Playwright / Puppeteer API — change the import
- Default **1 browser at a time**; contact support for more seats
- Chromium **151** · Linux & Windows

```javascript
import { launch } from "fingerprintchrome";

const browser = await launch();
const page = await browser.newPage();
await page.goto("https://example.com");
await browser.close();
```

Puppeteer: `import { launch } from "fingerprintchrome/puppeteer"`.

For tough sites, use a residential proxy:

```javascript
const browser = await launch({
  proxy: "http://user:pass@residential-proxy:port",
  geoip: true,
  headless: false,
  humanize: true,
});
```

---

## vs other tools

| | Stock Playwright | stealth plugins | fingerprintchrome |
|--|------------------|-----------------|-------------------|
| How it works | Stock Chrome | Inject JS / tweak flags | Patched Chromium binary |
| Easy to detect? | Yes | Often | Much harder |
| Breaks on Chrome updates? | — | Often | No (new binary) |

It does **not** auto-solve CAPTCHAs. It makes you look like a real user so fewer CAPTCHAs show up. You bring the proxy.

---

## Test results

| Check | Stock Playwright | fingerprintchrome |
|-------|------------------|-------------------|
| reCAPTCHA v3 | 0.1 (bot) | **~0.9** (human) |
| Cloudflare Turnstile | fail | **pass** |
| FingerprintJS | detected | **pass** |
| BrowserScan | detected | **normal** |
| `navigator.webdriver` | `true` | **`false`** |
| Headless UA leak | HeadlessChrome | **Chrome/151** |
| Automation / CDP flags | detected | **clean** |
| TLS fingerprint | wrong | **matches Chrome** |

Proxy and `headless` settings still matter — test on your own site.

---

## Quick start

```bash
pip3 install -r requirements.txt

# Download browser packages into archives/ (from GitHub Release)
FINGERPRINTCHROME_RELEASE_REPO=owner/fingerprintchrome ./scripts/fetch-archives.sh
# or copy linux/windows archives into archives/ yourself

python3 local_server.py
cd pkg && npm install
```

```bash
export FINGERPRINTCHROME_LICENSE_KEY=DEMO-KEY
export FINGERPRINTCHROME_LICENSE_API=http://127.0.0.1:19200
```

From Playwright:

```diff
- import { chromium } from "playwright";
- const browser = await chromium.launch();
+ import { launch } from "fingerprintchrome";
+ const browser = await launch();
```

---

## More seats

Default `DEMO-KEY` = **1** browser at a time (works out of the box).

Need more? Ask support for a key (same key works on multiple machines), then:

```bash
export FINGERPRINTCHROME_LICENSE_KEY='your-key'
```

Or put that one line in `~/.fingerprintchrome/license.key`.

---

## License

MIT (this wrapper). Browser binaries have their own terms.
