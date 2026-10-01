/**
 * fingerprintchrome-human — Human-like keyboard input.
 *
 * Stealth-aware: when a CDPSession is provided, shift symbols are typed
 * via CDP Input.dispatchKeyEvent (isTrusted=true, no evaluate stack trace).
 * Falls back to page.evaluate when no CDPSession is available.
 */
import type { Page, CDPSession } from 'playwright-core';
import type { RawKeyboard } from './mouse.js';
import { type HumanConfig } from './config.js';
export declare function pressWithDelay<Key>(press: (key: Key, options?: {
    delay?: number;
}) => Promise<void>, key: Key, options?: {
    delay?: number;
}, defaultDelay?: number): Promise<void>;
/**
 * Type text with human-like per-character timing, mistype simulation,
 * and realistic shift handling.
 *
 * @param cdpSession - If provided, shift symbols use CDP Input.dispatchKeyEvent
 *   producing isTrusted=true events with no evaluate stack trace.
 *   If null/undefined, falls back to page.evaluate (detectable).
 */
export declare function humanType(page: Page, raw: RawKeyboard, text: string, cfg: HumanConfig, cdpSession?: CDPSession | null): Promise<void>;
//# sourceMappingURL=keyboard.d.ts.map