/**
 * Playwright-style actionability checks for the humanize layer.
 *
 * Selector-based reads stay inside the CDP isolated world. ElementHandle paths
 * remain separate because they already identify an exact Playwright handle.
 */
import type { Page, Frame, ElementHandle } from 'playwright-core';
import { type StealthWorld } from './stealthDom.js';
export declare class ActionabilityError extends Error {
    selector: string;
    check: string;
    constructor(selector: string, check: string, message: string);
}
export declare class ElementNotAttachedError extends ActionabilityError {
    constructor(selector: string);
}
export declare class ElementNotVisibleError extends ActionabilityError {
    constructor(selector: string);
}
export declare class ElementNotStableError extends ActionabilityError {
    constructor(selector: string);
}
export declare class ElementNotEnabledError extends ActionabilityError {
    constructor(selector: string);
}
export declare class ElementNotEditableError extends ActionabilityError {
    constructor(selector: string);
}
export declare class ElementNotReceivingEventsError extends ActionabilityError {
    coveringTag: string;
    constructor(selector: string, coveringTag?: string);
}
export declare class ElementTargetChangedError extends ActionabilityError {
    constructor(selector: string);
}
export type CheckName = 'attached' | 'visible' | 'enabled' | 'editable' | 'pointer_events';
export declare const CHECKS_CLICK: ReadonlySet<CheckName>;
export declare const CHECKS_HOVER: ReadonlySet<CheckName>;
export declare const CHECKS_INPUT: ReadonlySet<CheckName>;
export declare const CHECKS_FOCUS: ReadonlySet<CheckName>;
export declare const CHECKS_CHECK: ReadonlySet<CheckName>;
export declare function ensureActionable(pageOrFrame: Page | Frame, selector: string, checks: ReadonlySet<CheckName>, timeout?: number, force?: boolean): Promise<void>;
export declare function ensureStable(pageOrFrame: Page | Frame, selector: string, timeout?: number): Promise<void>;
export declare function checkPointerEvents(pageOrFrame: Page | Frame, selector: string, targetId: number, gen: number, x: number, y: number, stealth?: StealthWorld | null, timeout?: number): Promise<void>;
export declare function ensureActionableHandle(el: ElementHandle, checks: ReadonlySet<CheckName>, timeout?: number, force?: boolean): Promise<void>;
export declare function checkPointerEventsHandle(el: ElementHandle, x: number, y: number, timeout?: number): Promise<void>;
//# sourceMappingURL=actionability.d.ts.map