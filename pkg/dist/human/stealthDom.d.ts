/** Versioned isolated-world DOM selector protocol; mirrors stealth_dom.py. */
export declare const PROTOCOL_VERSION = 2;
export declare const OK = "ok";
export declare const NOT_FOUND = "not_found";
export declare const UNSUPPORTED = "unsupported";
export declare const STALE = "stale";
export declare const EVALUATION_FAILED = "evaluation_failed";
export type StealthStatus = typeof OK | typeof NOT_FOUND | typeof UNSUPPORTED | typeof STALE | typeof EVALUATION_FAILED;
export declare class StealthDomError extends Error {
    constructor(message: string);
}
export declare class UnsupportedHumanizeSelectorError extends StealthDomError {
    constructor(selector: string);
}
export declare class StealthWorldUnavailableError extends StealthDomError {
    constructor();
}
export declare class StealthEvaluationError extends StealthDomError {
    constructor(selector: string);
}
export interface StealthWorld {
    evaluate(expression: string): Promise<any>;
}
export declare function getWorld(pageOrFrame: unknown): StealthWorld | null;
export interface StealthBox {
    x: number;
    y: number;
    width: number;
    height: number;
}
export interface StealthSnapshot {
    v: typeof PROTOCOL_VERSION;
    r: typeof OK;
    targetId: number;
    gen: number;
    attached: boolean;
    visible: boolean;
    enabled: boolean;
    editable: boolean;
    isInput: boolean;
    focused: boolean;
    checked: boolean | null;
    box: StealthBox | null;
}
/** Compatibility name used by the humanized action layer. */
export type SnapshotPayload = StealthSnapshot;
export interface StealthPointerPayload {
    v: typeof PROTOCOL_VERSION;
    r: typeof OK;
    targetId: number;
    gen: number;
    hit: boolean;
    covering?: string;
}
export interface ParsedResult {
    status: StealthStatus;
    data?: any;
}
export declare const VIEWPORT_JS = "(() => ({ width: window.innerWidth, height: window.innerHeight }))()";
export declare function buildSnapshotJs(selector: string): string;
export declare function buildBoxJs(selector: string): string;
export declare function buildActionableJs(selector: string): string;
export declare function buildValidateJs(selector: string, targetId: number, gen: number, x: number, y: number): string;
export declare function buildPointerJs(selector: string, x: number, y: number): string;
export declare function parseResult(raw: any): ParsedResult;
export declare function evalParsed(world: StealthWorld, expression: string): Promise<ParsedResult>;
//# sourceMappingURL=stealthDom.d.ts.map