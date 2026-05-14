// Plan colors — single source of truth for dashboard plan badges.
// Aligned with backend api/services/plan_config.py (S116a).
//
// Keep distinct from role colors (see roleColors in Organization.jsx).
// Plan 'consultant' was renamed to 'starter' in S116a — DO NOT confuse
// with role 'consultant' which still exists.

export const planColors = {
  free: '#666688',        // grey
  starter: '#3388ff',     // blue (same hue as old consultant plan)
  team: '#aa66ff',        // purple
  enterprise: '#00ff88',  // green
}

export const planColor = (plan) => planColors[plan] || '#666688'
