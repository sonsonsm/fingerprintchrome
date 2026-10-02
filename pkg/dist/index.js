/**
 * FingerprintChrome — Stealth Chromium for Node.js
 *
 * Default export uses Playwright. For Puppeteer, import from 'fingerprintchrome/puppeteer'.
 *
 * @example
 * ```ts
 * // Playwright (default)
 * import { launch } from 'fingerprintchrome';
 * const browser = await launch();
 *
 * // Puppeteer
 * import { launch } from 'fingerprintchrome/puppeteer';
 * const browser = await launch();
 * ```
 */
// Launch functions (Playwright API)
export { launch, launchContext, launchPersistentContext, buildLaunchOptions, buildContextOptions, humanizeBrowser } from "./playwright.js";
// Binary management
export { ensureBinary, clearCache, binaryInfo, checkForUpdate } from "./download.js";
// Config
export { CHROMIUM_VERSION, getDefaultStealthArgs } from "./config.js";
// License
export { validateLicense, FingerprintChromeLicenseError } from "./license.js";
//# sourceMappingURL=index.js.map