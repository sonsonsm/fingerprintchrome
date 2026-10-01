/**
 * Puppeteer launch wrapper for fingerprintchrome.
 * NOW WITH HUMANIZE SUPPORT — humanize: true enables human-like
 * mouse curves, keyboard timing, and scroll patterns (same as Playwright).
 */
import type { Browser } from "puppeteer-core";
import type { LaunchOptions } from "./types.js";
export { FingerprintChromeLicenseError } from "./license.js";
/**
 * Launch stealth Chromium browser via Puppeteer.
 *
 * @example
 * ```ts
 * import { launch } from 'fingerprintchrome/puppeteer';
 * // With humanize — human-like mouse, keyboard, scroll
 * const browser = await launch({ humanize: true });
 * const page = await browser.newPage();
 * await page.goto('https://example.com');
 * await page.click('#login');  // Bézier curve mouse movement
 * await page.type('#email', 'user@example.com');  // Per-character timing
 * ```
 */
export declare function launch(options?: LaunchOptions): Promise<Browser>;
/**
 * Launch stealth Chromium with a persistent user profile via Puppeteer.
 * Passes `userDataDir` to Puppeteer's launch options so cookies,
 * localStorage, and session data persist across launches.
 *
 * @example
 * ```ts
 * import { launchPersistentContext } from 'fingerprintchrome/puppeteer';
 * const browser = await launchPersistentContext({
 *   userDataDir: './chrome-profile',
 *   headless: false,
 *   proxy: 'http://user:pass@proxy:8080',
 * });
 * const page = await browser.newPage();
 * await page.goto('https://example.com');
 * await browser.close();
 * ```
 */
export declare function launchPersistentContext(options: LaunchOptions & {
    userDataDir: string;
}): Promise<Browser>;
//# sourceMappingURL=puppeteer.d.ts.map