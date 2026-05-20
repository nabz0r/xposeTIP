// S124 — formatters and helpers for Verified Provenance card.

const TIER_COLORS = {
  HIGH: { bg: 'rgba(0,255,136,0.15)', fg: '#00ff88', label: 'HIGH' },
  MEDIUM: { bg: 'rgba(255,204,0,0.15)', fg: '#ffcc00', label: 'MED' },
  LOW: { bg: 'rgba(255,136,0,0.15)', fg: '#ff8800', label: 'LOW' },
}

export function tierStyle(tier) {
  return TIER_COLORS[tier] || TIER_COLORS.LOW
}

export function confidenceColor(confidence) {
  if (confidence == null) return '#666688'
  if (confidence >= 0.80) return '#00ff88'
  if (confidence >= 0.60) return '#ffcc00'
  return '#ff8800'
}

// Relative time: "3d ago" / "1h ago" / "just now"
export function relativeTime(iso) {
  if (!iso) return null
  const then = new Date(iso).getTime()
  if (isNaN(then)) return null
  const diffSec = Math.floor((Date.now() - then) / 1000)
  if (diffSec < 60) return 'just now'
  if (diffSec < 3600) return `${Math.floor(diffSec / 60)}m ago`
  if (diffSec < 86400) return `${Math.floor(diffSec / 3600)}h ago`
  if (diffSec < 86400 * 30) return `${Math.floor(diffSec / 86400)}d ago`
  if (diffSec < 86400 * 365) return `${Math.floor(diffSec / 86400 / 30)}mo ago`
  return `${Math.floor(diffSec / 86400 / 365)}y ago`
}

// Confidence breakdown explanation
export function confidenceBreakdown(f) {
  const parts = []
  if (f.source_reliability != null) {
    parts.push(`${f.source_reliability.toFixed(2)} reliability`)
  }
  if (f.verified) {
    parts.push('× 1.0 verified')
  } else if (f.url) {
    parts.push('× 0.8 (has link)')
  } else {
    parts.push('× 0.6 (no link)')
  }
  if (f.cross_verified_count > 0) {
    parts.push('+ cross-verif boost')
  }
  return parts.join(' ')
}
