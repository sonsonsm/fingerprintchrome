/**
 * License validation and caching for FingerprintChrome Pro.
 * Mirrors Python fingerprintchrome/license.py.
 *
 * Handles license key resolution, server validation with local caching,
 * and Pro version checks.
 */
export interface LicenseInfo {
    valid: boolean;
    plan: string;
    expires: string | null;
}
/**
 * Result of a seat lookup: the count, the cap it counts against, and the reason
 * either is missing.
 *
 * state:
 *   "ok"          active is a real number (0 is a real answer, not an error)
 *   "unreachable" never got an answer — DNS, refused, timeout, TLS
 *   "denied"      the server refused; `reason` carries its error code
 *   "unknown"     the server is up and the key is fine, but it cannot count
 *                 right now (leaseless mode, or its seat store is unreachable)
 *
 * limit is null whenever the server declined to state a cap: unlimited, an
 * unrecognised plan, or a server too old to send the field. Callers must fall back
 * to the bare count, never invent a denominator.
 */
export interface SessionSeats {
    active: number | null;
    limit: number | null;
    state: "ok" | "unreachable" | "denied" | "unknown";
    reason: string | null;
}
export interface ProReleaseInfo {
    version: string;
    requestedChannel: "stable" | "preview";
    resolvedChannel: "stable" | "preview";
    fallback: boolean;
}
/**
 * The Pro binary refused to run for a license reason. Thrown when a launch
 * fails and the browser process exited with one of the Pro binary's license
 * exit codes, carrying a human-readable reason instead of the opaque
 * "target/browser closed" error the caller would otherwise see.
 */
export declare class FingerprintChromeLicenseError extends Error {
    constructor(message: string, options?: {
        cause?: unknown;
    });
}
/**
 * Map a launch-failure message to a license reason, or null. Returns the human
 * message when the browser process exited with a known license exit code, else
 * null so a genuine crash propagates unchanged.
 */
export declare function licenseErrorMessage(errorText: string): string | null;
/**
 * Return a FingerprintChromeLicenseError if a launch failure was a license deny,
 * else null so the original error propagates unchanged.
 */
export declare function licenseErrorFrom(err: unknown): FingerprintChromeLicenseError | null;
export declare const LICENSE_STATUS_FILE_ENV = "CLOAKBROWSER_LICENSE_STATUS_FILE";
/**
 * Map a raw license exit code (76-79) to a FingerprintChromeLicenseError, or null
 * for any code that is not a known license denial (so a genuine crash is never
 * mislabelled). Companion to licenseErrorMessage for the post-handshake,
 * file-based path where we hold the integer directly.
 */
export declare function licenseErrorForCode(code: number): FingerprintChromeLicenseError | null;
/**
 * Read and consume a denial file written by the binary, returning its code.
 * The file holds a single JSON integer (the exit code). Reading is destructive:
 * the file is unlinked afterwards so a later launch can't see a stale code, but
 * the observed code is cached in-process so a concurrent second guarded call
 * still surfaces the denial. Any problem — absent, unreadable, or not a valid
 * int — yields null.
 */
export declare function readDenialFile(filePath: string): number | null;
export declare function mintDenialFile(): string | undefined;
/**
 * Guard every public method of `target` (a browser, context, or page) so a
 * post-handshake license denial surfaces as FingerprintChromeLicenseError on the
 * user's first failing call — whichever method that is.
 *
 * A denial that lands after the driver connected kills the browser without a
 * launch failure; the user's next call would otherwise throw a bare
 * TargetClosedError. Each wrapped method checks the denial file the binary
 * wrote — on error AND on success (the binary writes the file the instant it's
 * over cap but keeps serving blank responses for ~1s before it exits, so a fast
 * flow that never throws must still surface it). A genuine, non-license error
 * propagates unchanged. Factory methods (newPage/newContext/…) additionally
 * guard the object they return, so a page obtained after launch is covered too.
 *
 * Sync-ness is preserved: an async method's promise is chained, a sync method
 * (`url()`, `isClosed()`, `on()`) returns its value directly — wrapping those in
 * an async function would break them. Mirrors Python _install_license_guard.
 */
export declare function installLicenseGuard(target: any, denialPath: string): void;
/**
 * Source of a resolved license key.  Determines whether env injection
 * into the child browser process is needed.
 *
 * - ``param`` / ``custom_file`` -> must inject (binary can't see these).
 * - ``env`` -> already in parent ``os.environ``, child inherits naturally.
 * - ``default_file`` -> binary reads ``~/.fingerprintchrome/license.key`` directly.
 * - ``none`` / ``undefined`` -> no key.
 */
export type LicenseKeySource = "param" | "env" | "default_file" | "custom_file" | "none";
/**
 * Like ``resolveLicenseKey`` but also returns the source for env-injection
 * decisions.  Internal; consumers should use ``resolveLicenseKey`` or
 * ``buildLaunchEnv``.
 */
export declare function resolveLicenseKeyWithSource(licenseKey?: string): {
    key: string | undefined;
    source: LicenseKeySource;
};
/**
 * Resolve the license key: explicit param > env var > file > undefined.
 */
export declare function resolveLicenseKey(licenseKey?: string): string | undefined;
/**
 * Build a child-process env dict with any needed license key injection.
 *
 * The Pro binary reads ``CLOAKBROWSER_LICENSE_KEY`` from its own process
 * environment at startup.  This helper merges the resolved key into the
 * child process env dict **only** when injection is necessary:
 *
 * * **param** / **custom_file** source -> inject into child env.
 * * **env** source -> child inherits from parent (no injection).
 * * **default_file** source -> binary reads the file directly (no injection),
 *   unless a custom userEnv is passed (Playwright replaces the child env and
 *   can drop HOME, hiding the file), in which case the key is injected.
 *
 * When *userEnv* is provided it is used as the base (Playwright replaces
 * the child env entirely when ``env`` is set), with the key injected only
 * when needed.
 *
 * Returns ``undefined`` when no injection is needed and no custom userEnv
 * was given — Playwright treats ``env=undefined`` as "inherit parent env".
 */
export declare function buildLaunchEnv(licenseKey?: string, userEnv?: Record<string, string | undefined>, statusFile?: string): Record<string, string> | undefined;
/**
 * Validate a license key with the FingerprintChrome server.
 *
 * Checks a local file cache first (24h TTL). Falls back to stale
 * cache if the server is unreachable.
 *
 * Returns LicenseInfo if validation succeeded, null on total failure.
 */
export declare function validateLicense(licenseKey: string): Promise<LicenseInfo | null>;
/** Get the server-resolved Pro release and channel for this platform. */
export declare function getProLatestRelease(releaseChannel?: string): Promise<ProReleaseInfo | null>;
/** Get only the version from the server-resolved Pro release. */
export declare function getProLatestVersion(releaseChannel?: string): Promise<string | null>;
/**
 * Seats held right now, the cap they count against, and why either is missing.
 *
 * Deliberately NOT cached: a cached seat count is a wrong seat count.
 *
 * Six different things can stop us answering — no route to the host, a timeout, a
 * 403 for a dead key, a 429, the server reporting the count as unknown in leaseless
 * mode, and its seat store being unreachable. They used to collapse into one bare
 * null, so `info` printed the same "unavailable" for "your key is dead" and "our
 * backend is degraded, you are fine". `state` keeps them apart.
 */
export declare function getSessionSeats(licenseKey: string): Promise<SessionSeats>;
/**
 * How many concurrent sessions (seats) this license is holding right now.
 *
 * Kept for callers outside `info` that only want the number. Prefer
 * getSessionSeats(), which also carries the cap and the reason a lookup failed.
 */
export declare function getActiveSessionCount(licenseKey: string): Promise<number | null>;
//# sourceMappingURL=license.d.ts.map