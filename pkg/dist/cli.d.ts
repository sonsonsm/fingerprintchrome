#!/usr/bin/env node
/**
 * CLI for fingerprintchrome — download and manage the stealth Chromium binary.
 *
 * Usage:
 *   npx fingerprintchrome install      # Download binary (with progress)
 *   npx fingerprintchrome info         # Environment + binary diagnostics
 *   npx fingerprintchrome doctor       # Alias for info
 *   npx fingerprintchrome update       # Check for and download newer binary
 *   npx fingerprintchrome clear-cache  # Remove cached binaries
 */
export declare function collectDiagnostics(quick: boolean, proxy?: string): Promise<Record<string, unknown>>;
interface SeatSection {
    active?: number | null;
    limit?: number | null;
    state?: string;
    reason?: string | null;
}
/** Render the seat lookup. Kept identical in the Python and .NET wrappers. */
export declare function formatSeats(sessions: SeatSection): string;
export {};
//# sourceMappingURL=cli.d.ts.map