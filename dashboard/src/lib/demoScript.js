// S249 — Deterministic scan-replay script. No network. The Demo page consumes
// `buildTimeline()` to drive: fakeScan (-> PixelCat pose via phaseFromScan),
// the DemoFlow backdrop layer that lights up, and the status-stream ticker.
import { SOURCE_COUNT } from '../components/landing/constants'

export const PACE = 1.0 // ×1.0 ≈ 4 min, ×1.6 ≈ 7 min

// 5 acts. `fakeScan` shape matches what phaseFromScan() expects in PixelCat.jsx.
// `activeLayer` matches DemoFlow's layer ids: inputs / osint / graph / reports / bfp.
export const ACTS = [
  {
    id: 'resolving',
    title: 'Act 1 · Resolving',
    accent: '#888',
    durationMs: 25_000,
    activeLayer: 'inputs',
    fakeScan: { status: 'queued', module_progress: {}, cascade_state: null },
    pitch: 'One email. Everything starts there.',
    realStatuses: [
      'Resolving email…',
      'Validating MX records…',
      'Checking DNS, DMARC, SPF…',
    ],
  },
  {
    id: 'hunting',
    title: 'Act 2 · Hunting',
    accent: '#3388ff',
    durationMs: 90_000,
    activeLayer: 'osint',
    fakeScan: {
      status: 'running',
      module_progress: { email_validator: 'completed', scraper_engine: 'running' },
      cascade_state: null,
    },
    pitch: `${SOURCE_COUNT} OSINT sources. 28 scanners. The full surface.`,
    realStatuses: [
      'Querying 28 scanners in parallel…',
      'Holehe across 56 platforms…',
      'GitHub / GitLab discovery…',
      'Cross-checking breach databases…',
      `Sweeping ${SOURCE_COUNT} data-driven scrapers…`,
      'Found {social_accounts} accounts…',
      'Found {breaches} breach references…',
    ],
  },
  {
    id: 'connecting',
    title: 'Act 3 · Connecting',
    accent: '#888',
    durationMs: 60_000,
    activeLayer: 'graph',
    fakeScan: {
      status: 'completed',
      module_progress: { scraper_engine: 'completed' },
      cascade_state: 'gathering',
    },
    pitch: 'We connect — cross-reference — propagate.',
    realStatuses: [
      'Building identity graph…',
      'PageRank confidence propagation (20 iter)…',
      'Cross-verifying findings…',
      'Resolving timezone signal…',
      'Resolving geography → {country}…',
      'Detecting language → {lang}…',
    ],
  },
  {
    id: 'profiling',
    title: 'Act 4 · Profiling',
    accent: '#00ff88',
    durationMs: 70_000,
    activeLayer: 'bfp',
    fakeScan: {
      status: 'completed',
      module_progress: { scraper_engine: 'completed' },
      cascade_state: 'computing',
    },
    pitch: 'From IOC to person. The BFP layer crystallizes.',
    realStatuses: [
      'Computing 11-axis behavioral radar…',
      'Locality-sensitive behavioral hash (MinHash 128)…',
      'Anchoring claim log (RFC-6962 Merkle)…',
      'Discovering behavioral cluster (K=3)…',
      'Found {cluster_count} peers in cluster prefix {hash_prefix}…',
    ],
  },
  {
    id: 'identity',
    title: 'Act 5 · Identity',
    accent: '#00ff88',
    durationMs: 0, // reveal — hold until user advances
    activeLayer: 'reports',
    fakeScan: {
      status: 'completed',
      module_progress: { scraper_engine: 'completed' },
      cascade_state: 'done',
    },
    pitch: 'The subject takes the reading back. The inversion.',
    realStatuses: [
      'Finalizing identity portrait…',
      'Subject can read what the internet reads about them.',
    ],
  },
]

// Flavor pool ≥ 40. Gerunds, food/lab metaphors. Used between real-status beats.
export const FLAVOR_POOL = [
  'Moistering identities…',
  'Steeping in metadata…',
  'Whisking signals…',
  'Caramelizing the graph…',
  'Proofing the fingerprint…',
  'Marinating timestamps…',
  'Folding in cross-refs…',
  'Tempering the radar…',
  'Reducing noise…',
  'Glazing the timeline…',
  'Distilling intent…',
  'Decanting handles…',
  'Brining geolocations…',
  'Searing the breach corpus…',
  'Macerating breach dumps…',
  'Sifting the username space…',
  'Roasting domain whois…',
  'Curing the persona graph…',
  'Pickling pasted secrets…',
  'Toasting the activity rhythm…',
  'Blanching usernames…',
  'Confiting the social profiles…',
  'Smoking the cascade queue…',
  'Plating the identity portrait…',
  'Reticulating splines…',
  'Buttering the merkle tree…',
  'Frosting confidence scores…',
  'Sautéing for 2m on each side…',
  'Skewering correlations…',
  'Mulching the OSINT lake…',
  'Whipping the entropy budget…',
  'Drizzling cross-verifications…',
  'Folding the keystroke rhythm in…',
  'Slow-roasting the behavioral hash…',
  'Sifting handles through 4× sieves…',
  'Re-emulsifying broken edges…',
  'Tossing the cascade salad…',
  'Reducing the username heatmap…',
  'Plating the reveal…',
  'Stirring 11 axes counter-clockwise…',
  'Garnishing with merkle leaves…',
  'Aerating the trust graph…',
  'Resting the fingerprint for 30s…',
]

// Substitute {placeholders} from the snapshot.
function fill(template, snapshot) {
  return template.replace(/\{(\w+)\}/g, (_, key) => {
    if (key === 'social_accounts') return snapshot.counts?.social_accounts ?? '—'
    if (key === 'breaches') return snapshot.counts?.breaches ?? '—'
    if (key === 'country') return snapshot.profile?.geo_consistency?.primary_country_name
      || snapshot.profile?.geo_consistency?.primary_country
      || snapshot.target?.country_code
      || '—'
    if (key === 'lang') {
      const code = snapshot.profile?.languages?.primary
      if (!code) return '—'
      return code.toUpperCase()
    }
    if (key === 'cluster_count') return snapshot.cluster?.count ?? '—'
    if (key === 'hash_prefix') return (snapshot.cluster?.prefix || '').slice(0, 8) || '—'
    return ''
  })
}

/**
 * Build the deterministic beat list driving the page. Returns
 *   [{ tMs: number, type: 'status'|'layer'|'act'|'reveal', payload }, …]
 * Beats are pre-baked relative to act starts (tMs cumulative). The page
 * walks them with setTimeout. PACE > 1 stretches everything proportionally.
 */
export function buildTimeline(snapshot, pace = PACE) {
  const beats = []
  let cursor = 0
  ACTS.forEach((act, idx) => {
    const dur = Math.round(act.durationMs * pace)
    beats.push({ tMs: cursor, type: 'act', payload: { index: idx, act } })
    beats.push({ tMs: cursor, type: 'layer', payload: { layer: act.activeLayer } })

    if (act.id === 'identity') {
      // Reveal beat — page transitions out of the scripted stream
      beats.push({ tMs: cursor + 600, type: 'reveal', payload: {} })
      return
    }

    // Interleave real statuses + flavor across the act window
    const filled = act.realStatuses.map((s) => fill(s, snapshot))
    const flavor = pickFlavor(idx, 12)
    const stream = []
    let f = 0
    filled.forEach((real, i) => {
      stream.push({ kind: 'real', text: real })
      // Insert 1–2 flavor lines after each real one (except the very last)
      if (i < filled.length - 1) {
        const n = 1 + (i % 2)
        for (let k = 0; k < n && f < flavor.length; k++, f++) {
          stream.push({ kind: 'flavor', text: flavor[f] })
        }
      }
    })
    // Distribute evenly across the act window with small jitter
    const step = stream.length > 0 ? dur / (stream.length + 1) : dur
    stream.forEach((s, i) => {
      const jitter = ((i * 53) % 13) * 40 // deterministic small offset
      beats.push({
        tMs: cursor + Math.round(step * (i + 1) + jitter),
        type: 'status',
        payload: s,
      })
    })
    cursor += dur
  })
  return beats
}

// Deterministic flavor picker — same act index always picks the same lines.
function pickFlavor(actIndex, count) {
  const out = []
  let i = (actIndex * 7 + 3) % FLAVOR_POOL.length
  while (out.length < count) {
    out.push(FLAVOR_POOL[i])
    i = (i + 1 + actIndex) % FLAVOR_POOL.length
  }
  return out
}
