// Avatar seed fallback — single source of truth.
// Used by ProfileHeader, Dashboard, Targets, UserPreview (post-S137 centralization).
//
// IMPORTANT — this is NOT a strict mirror of backend _email_only_avatar_seed
// (api/routers/targets.py). The backend uses MD5 → 9-key seed; this fallback
// uses a JS bit-shift hash → 4-key seed (enough for GenerativeAvatar minimum
// render). They produce different avatars for the same email by design.
//
// Post-S135 the backend always populates fingerprint_avatar_seed, so this
// fallback only fires on:
//   - legacy clients hitting cached API responses
//   - test fixtures missing the field
//   - transitional state during a deploy
//
// Defense in depth — keeps avatars deterministic per-email even if the
// backend value is briefly missing. Do NOT attempt to match backend output
// without also rewriting the JS hash function (out of scope here).

export const fallbackSeed = (email) => {
  let hash = 0
  for (let i = 0; i < (email || '').length; i++) {
    hash = ((hash << 5) - hash) + email.charCodeAt(i)
    hash |= 0
  }
  const eh = Math.abs(hash)
  return {
    email_hash: eh % 10000,
    hue: (eh % 60) + 120,
    num_points: 3,
    rotation: eh % 360,
  }
}
