/**
 * Human-like behavioral layer for fingerprintchrome (JS/TS).
 *
 * Activated via humanize: true in launch() / launchContext().
 * Patches page methods to use Bezier mouse curves, realistic typing, and smooth scrolling.
 *
 * Stealth-aware (fixes #110, #512):
 *   - Selector resolution, state, geometry, and revalidation use the CDP isolated world
 *   - Shift symbol typing uses CDP Input.dispatchKeyEvent for isTrusted=true events
 *   - Unsupported selectors and isolated-world failures raise typed errors
 *
 * Patches all interaction methods:
 * click, dblclick, hover, type, fill, check, uncheck, selectOption,
 * press, pressSequentially, tap, dragTo, clear + Frame-level equivalents.
 *
 * ELEMENTHANDLE-LEVEL:
 *   click, dblclick, hover, type, fill, press, selectOption,
 *   check, uncheck, setChecked, tap, focus
 *   + $, $$, waitForSelector (nested elements are also patched)
 *
 * page.$(), page.$$(), page.waitForSelector() and Frame equivalents
 * return patched ElementHandles automatically.
 */
import type { Browser, BrowserContext, Page } from 'playwright-core';
import { type HumanConfig } from './config.js';
export { HumanConfig, resolveConfig, mergeConfig } from './config.js';
export { humanMove, humanClick, clickTarget, humanIdle } from './mouse.js';
export { humanType } from './keyboard.js';
export { scrollToElement, humanScrollIntoView } from './scroll.js';
export { patchSingleElementHandle } from './elementhandle.js';
export { ActionabilityError, ElementNotAttachedError, ElementNotVisibleError, ElementNotStableError, ElementNotEnabledError, ElementNotEditableError, ElementNotReceivingEventsError, ElementTargetChangedError, } from './actionability.js';
export { StealthDomError, UnsupportedHumanizeSelectorError, StealthWorldUnavailableError, StealthEvaluationError, } from './stealthDom.js';
declare class CursorState {
    x: number;
    y: number;
    initialized: boolean;
}
/**
 * Replace page methods with human-like implementations.
 */
declare function patchPage(page: Page, cfg: HumanConfig, cursor: CursorState): void;
declare function patchContext(context: BrowserContext, cfg: HumanConfig): void;
export declare function patchBrowser(browser: Browser, cfg: HumanConfig): void;
export { patchContext, patchPage };
//# sourceMappingURL=index.d.ts.map