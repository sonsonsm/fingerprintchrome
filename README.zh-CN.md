# fingerprintchrome

[English](README.md) | [简体中文](README.zh-CN.md)

### 能过机器人检测的隐身浏览器。

不是改几个参数，也不是往页面里塞脚本。指纹在 Chromium 里改完再编译——网站看到的就是正常 Chrome。

- 过 **Cloudflare 人机验证**、**FingerprintJS**、**BrowserScan** 等 30+ 检测
- **reCAPTCHA v3 约 0.9**（接近真人）
- 类人鼠标 / 键盘 / 滚动（`humanize: true`）
- 还是 Playwright / Puppeteer 写法，换个 import
- 默认同时开 **1** 个浏览器；要多开联系后台要 key
- Chromium **151** · 支持 Linux、Windows

```javascript
import { launch } from "fingerprintchrome";

const browser = await launch();
const page = await browser.newPage();
await page.goto("https://example.com");
await browser.close();
```

Puppeteer：`import { launch } from "fingerprintchrome/puppeteer"`。

难开的站，建议配住宅代理：

```javascript
const browser = await launch({
  proxy: "http://user:pass@residential-proxy:port",
  geoip: true,
  headless: false,
  humanize: true,
});
```

---

## 和其他方案比

| | 原版 Playwright | stealth 插件 | fingerprintchrome |
|--|-----------------|--------------|-------------------|
| 原理 | 普通 Chrome | 注入脚本 / 改参数 | 改过的 Chromium 安装包 |
| 容易被识破？ | 是 | 经常 | 难得多 |
| Chrome 升级就挂？ | — | 经常 | 不用（换新包） |

**不会自动帮你过验证码。** 是让你更像真人，少弹验证码。代理自己准备。

---

## 检测结果

| 检测 | 原版 Playwright | fingerprintchrome |
|------|-----------------|-------------------|
| reCAPTCHA v3 | 0.1（机器人） | **约 0.9**（真人） |
| Cloudflare 人机验证 | 不过 | **过** |
| FingerprintJS | 被识别 | **过** |
| BrowserScan | 被识别 | **正常** |
| `navigator.webdriver` | `true` | **`false`** |
| 无头浏览器特征 | HeadlessChrome | **Chrome/151** |
| 自动化特征 | 能查出来 | **干净** |
| 网络指纹 | 对不上 | **和 Chrome 一样** |

代理、是否无头窗口，都会影响结果——用你自己的目标站测一下。

---

## 快速开始

```bash
pip3 install -r requirements.txt

# 从 GitHub Release 下载浏览器安装包到 archives/
FINGERPRINTCHROME_RELEASE_REPO=owner/fingerprintchrome ./scripts/fetch-archives.sh
# 或自己把 linux/windows 包放进 archives/

python3 local_server.py
cd pkg && npm install
```

```bash
export FINGERPRINTCHROME_LICENSE_KEY=DEMO-KEY
export FINGERPRINTCHROME_LICENSE_API=http://127.0.0.1:19200
```

从 Playwright 换过来：

```diff
- import { chromium } from "playwright";
- const browser = await chromium.launch();
+ import { launch } from "fingerprintchrome";
+ const browser = await launch();
```

---

## 多开席位

默认 `DEMO-KEY` = 同时只能开 **1** 个浏览器（装上就能用，不用申请）。

要多开：联系后台拿 key（同一把 key 可在多台机器用），然后：

```bash
export FINGERPRINTCHROME_LICENSE_KEY='你的key'
```

或者写到 `~/.fingerprintchrome/license.key`（就一行）。

---

## 许可证

本仓库封装代码 MIT。浏览器安装包另有条款。
