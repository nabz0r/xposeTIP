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
