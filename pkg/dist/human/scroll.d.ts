/**
 * fingerprintchrome-human — Human-like scrolling via mouse wheel events.
 *
 * Selector geometry and live DOM scroll state are read only through the CDP
 * isolated world. ElementHandle callers may still supply their own exact box.
 */
import type { Page } from 'playwright-core';
import { type HumanConfig } from './config.js';
import { type RawMouse } from './mouse.js';
export interface ElementBounds {
    x: number;
    y: number;
    width: number;
    height: number;
    targetId?: number;
}
export interface SelectorBounds extends ElementBounds {
    targetId: number;
    gen: number;
}
export declare function humanScrollIntoView<T extends ElementBounds>(page: Page, raw: RawMouse, getBox: () => Promise<T | null>, cursorX: number, cursorY: number, cfg: HumanConfig): Promise<{
    box: T;
    cursorX: number;
    cursorY: number;
    didScroll: boolean;
}>;
export declare function scrollToElement(page: Page, raw: RawMouse, selector: string, cursorX: number, cursorY: number, cfg: HumanConfig, timeout?: number): Promise<{
    box: SelectorBounds;
    cursorX: number;
    cursorY: number;
    didScroll: boolean;
}>;
export declare function getElementBox(page: Page, selector: string, timeout?: number): Promise<SelectorBounds | null>;
//# sourceMappingURL=scroll.d.ts.map