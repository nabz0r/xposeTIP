/**
 * Helpers for normalizing scan.module_progress values.
 *
 * Background: `module_progress` is a {module_name: status} map where most
 * modules store status as a flat string ('completed', 'running', 'failed',
 * 'skipped'). The `scraper_engine` module dispatches many sub-scrapers and
 * may store its status as a {scraper_name: status} sub-dict instead — this
 * format depends on the scan's age (post-Sprint 45 telemetry vs older).
 *
 * Frontend code that does `progress.x === 'running'` or renders `{progress.x}`
 * directly breaks on the dict shape. These helpers normalize both shapes.
 */

/**
 * Aggregate a module status value to a single status string.
 * Dict values use worst-case prioritization (failed > running > completed/skipped > mixed).
 *
 * @param {string|object|null|undefined} value
 * @returns {'completed'|'running'|'failed'|'skipped'|'mixed'|'unknown'}
 */
export function normalizeModuleStatus(value) {
  if (typeof value === 'string') return value
  if (value && typeof value === 'object') {
    const values = Object.values(value).filter(v => typeof v === 'string')
    if (values.length === 0) return 'unknown'
    if (values.includes('failed')) return 'failed'
    if (values.includes('running')) return 'running'
    if (values.every(v => v === 'completed')) return 'completed'
    if (values.every(v => v === 'skipped')) return 'skipped'
    return 'mixed'
  }
  return 'unknown'
}

/**
 * Format a module status value for display.
 * String → returned as-is.
 * Dict → "N completed / M failed" style summary (largest count first).
 *
 * @param {string|object|null|undefined} value
 * @returns {string}
 */
export function formatModuleStatus(value) {
  if (typeof value === 'string') return value
  if (value && typeof value === 'object') {
    const counts = {}
    for (const v of Object.values(value)) {
      const k = typeof v === 'string' ? v : 'unknown'
      counts[k] = (counts[k] || 0) + 1
    }
    if (Object.keys(counts).length === 0) return 'unknown'
    return Object.entries(counts)
      .sort((a, b) => b[1] - a[1])
      .map(([k, c]) => `${c} ${k}`)
      .join(' / ')
  }
  return String(value ?? 'unknown')
}
