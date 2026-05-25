/**
 * catSeed — derive PixelCat trait palette from the same fingerprint_avatar_seed
 * that drives GenerativeAvatar. Same seed → same cat. Defensive null-fallback.
 *
 * Mapping:
 *   email_hash    → fur color   (8 options)
 *   hue           → eye color   (6 options)
 *   rotation      → collar      (8 options)
 *   num_points    → tail variant (0..3)
 *
 * Used by PixelCat.jsx. Lives in lib/ so other tabs can derive a cat without
 * importing the heavy component.
 */

import { fallbackSeed } from './avatar'

const FUR_PALETTE = [
  '#1a1a1a', '#4a3728', '#8B4513', '#DAA520',
  '#D2691E', '#A52A2A', '#C0C0C0', '#F0E68C',
]

const EYE_PALETTE = [
  '#00ff88', '#2244aa', '#44aa44', '#886633', '#aa4444', '#44aaaa',
]

const COLLAR_PALETTE = [
  '#e94560', '#00ff88', '#3388ff', '#ffcc00',
  '#ff8800', '#aa44aa', '#666666', '#ffffff',
]

const idx = (v, mod) => Math.abs((v | 0)) % mod

export function deriveCatTraits(seed) {
  const s = seed || { email_hash: 0, hue: 0, num_points: 5, rotation: 0 }
  return {
    fur:    FUR_PALETTE[idx(s.email_hash, FUR_PALETTE.length)],
    eye:    EYE_PALETTE[idx(s.hue, EYE_PALETTE.length)],
    collar: COLLAR_PALETTE[idx(s.rotation, COLLAR_PALETTE.length)],
    tail:   idx(s.num_points, 4),
    belly:  '#3a3a3a',
    nose:   '#ff5588',
  }
}

export function catFromEmail(email) {
  return deriveCatTraits(fallbackSeed(email))
}

// ─────────────────────────────────────────────────────────────
// S221 — behavioral detail layer
// Derived from Target.bfp_behavioral_hash_v1 (hex string, SHA-3 trunc).
// Null/empty hash → all defaults → cat renders as the S219 baseline.
// ─────────────────────────────────────────────────────────────

const PATTERNS    = ['solid', 'tabby', 'spots', 'bicolor', 'calico', 'ticked']
const ACCESSORIES = ['none', 'glasses', 'bowtie', 'scarf', 'badge']
const MARKINGS    = ['none', 'mask', 'blaze', 'whiskers', 'nose_spot']
const EXPRESSIONS = ['chill', 'alert', 'curious', 'sleepy']

/**
 * Derive the behavioral detail layer from a BFP behavioral hash.
 *
 * Hash format: hex string ≥ 16 chars (SHA-3-256 truncated or full).
 * Null / empty / malformed → all-default response (matches S219 baseline,
 * so pre-scan / data-starved targets render unchanged).
 *
 * Returns: { pattern, accessory, marking, expression } — string keys
 * matching the PATTERNS / ACCESSORIES / MARKINGS / EXPRESSIONS constants.
 */
export function deriveBehavioralDetails(hash) {
  if (!hash || typeof hash !== 'string' || hash.length < 16) {
    return { pattern: 'solid', accessory: 'none', marking: 'none', expression: 'chill' }
  }
  const safe = (start, end) => {
    const slice = hash.slice(start, end)
    const n = parseInt(slice, 16)
    return Number.isNaN(n) ? 0 : n
  }
  return {
    pattern:    PATTERNS[safe(0, 4)     % PATTERNS.length],
    accessory:  ACCESSORIES[safe(4, 8)  % ACCESSORIES.length],
    marking:    MARKINGS[safe(8, 12)    % MARKINGS.length],
    expression: EXPRESSIONS[safe(12,16) % EXPRESSIONS.length],
  }
}
