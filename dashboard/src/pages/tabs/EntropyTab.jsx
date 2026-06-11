// S267 — Entropy tab. Renders the information-theoretic identifying-bits ledger
// the engine computes per target (confidence.entropy_breakdown). A self-standing
// layer: how much of someone's ~33 identity bits the open web has resolved, the
// per-axis breakdown, what is NOT yet measured, and the budget gauge — returned to
// the subject as a ledger, not held over them.

const GRID = '0.035'

// Colour = REAL quality state of each axis (the engine does not emit a per-axis
// veracity number, so we never fabricate one):
//   measured     — real prevalence from priors (country, provider) → solid blue
//   coarse       — v0 estimate (name common/rare) → amber, hatched
//   discounted   — governor-2 correlated, counted via another axis (bits=0) → grey
const AXIS_COLORS = {
  measured: '#3388ff',
  coarse: '#ff8800',
  discounted: '#888888',
}

function axisQuality(a) {
  if (a?.correlated_with) return 'discounted'
  if (a?.coarse) return 'coarse'
  return 'measured'
}

function EmptyState() {
  return (
    <div className="py-16 text-center">
      <div className="text-3xl font-mono text-gray-600 mb-3">— bits</div>
      <p className="text-gray-400 text-sm">
        Entropy not yet computed for this target.
      </p>
      <p className="text-gray-600 text-xs mt-1">
        It is derived at profile aggregation — runs on the next recompute or scan.
      </p>
    </div>
  )
}

export default function EntropyTab({ profile }) {
  const eb = profile?.confidence?.entropy_breakdown
  if (!eb) return <EmptyState />

  const bits = Number(eb.identifying_bits ?? profile?.confidence?.identifying_bits ?? 0)
  const unique = Number(eb.global_unique_bits ?? 33)
  const cap = Number(eb.cap_bits ?? 20)
  const set = eb.anonymity_set
  const axes = eb.by_axis || {}
  const unknown = eb.axes_unknown || []
  const capped = !!eb.capped

  const consumedPct = Math.max(0, Math.min(100, (bits / unique) * 100))
  const capPct = Math.max(0, Math.min(100, (cap / unique) * 100))

  // gauge segments — width PROPORTIONAL to bits (not equal cells), discounted
  // (0-bit) axes contribute no width but stay in the ledger below.
  const segs = Object.entries(axes)
    .map(([key, a]) => ({ key, a, bits: Number(a.bits || 0), q: axisQuality(a) }))
    .filter(s => s.bits > 0)
    .sort((x, y) => y.bits - x.bits)

  const fmtSet = (n) => {
    if (n == null) return '—'
    if (n >= 1e6) return `~${(n / 1e6).toFixed(1)}M`
    if (n >= 1e3) return `~${(n / 1e3).toFixed(1)}k`
    return `~${n}`
  }

  return (
    <div className="space-y-6 py-2" style={{
      backgroundImage: `linear-gradient(rgba(255,255,255,${GRID}) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,${GRID}) 1px, transparent 1px)`,
      backgroundSize: '24px 24px',
    }}>
      <style>{`
        @media (prefers-reduced-motion: reduce) { .ent-anim { transition: none !important; } }
        .ent-hatch { background-image: repeating-linear-gradient(45deg, transparent, transparent 3px, rgba(0,0,0,0.35) 3px, rgba(0,0,0,0.35) 6px); }
        .ent-seg:focus-visible { outline: 2px solid #00ff88; outline-offset: 2px; }
      `}</style>

      {/* Headline */}
      <div className="flex items-end gap-3 flex-wrap">
        <div className="font-mono text-4xl text-[#3388ff] leading-none">{bits.toFixed(1)}</div>
        <div className="text-gray-400 text-sm pb-1">
          of <span className="font-mono text-gray-300">{unique}</span> identity bits resolved
        </div>
        {capped && (
          <span className="text-[10px] font-mono px-1.5 py-0.5 rounded mb-1" style={{ color: '#888', border: '1px solid #888' }}
            title="Capped at the OSINT-only ceiling — public data never asserts global uniqueness.">
            capped at {cap}
          </span>
        )}
      </div>
      <div className="text-sm text-gray-300">
        {eb.verdict} · anonymity set <span className="font-mono text-[#3388ff]">{fmtSet(set)}</span> people
      </div>

      {/* Budget gauge — segment widths proportional to bits */}
      <div className="mt-2">
        <div className="relative h-6 rounded bg-[#12121a] border border-[#1e1e2e] overflow-hidden flex">
          {segs.map(s => (
            <div key={s.key}
              className={`ent-seg ent-anim ${s.q === 'coarse' ? 'ent-hatch' : ''}`}
              tabIndex={0}
              title={`${s.key}: ${s.bits.toFixed(2)} bits (${s.q})`}
              style={{ width: `${(s.bits / unique) * 100}%`, background: AXIS_COLORS[s.q], transition: 'width .4s ease' }}
            />
          ))}
        </div>
        {/* markers under the bar */}
        <div className="relative h-5 mt-1 text-[10px] font-mono text-gray-500">
          <div className="absolute top-0 -translate-x-1/2" style={{ left: `${consumedPct}%`, color: '#3388ff' }}>▲ now {bits.toFixed(1)}</div>
          <div className="absolute top-0 -translate-x-1/2" style={{ left: `${capPct}%` }}>┊ OSINT cap {cap}</div>
          <div className="absolute top-0 right-0">unique 33 ┊</div>
        </div>
      </div>

      {/* Axis ledger */}
      <div>
        <div className="text-xs uppercase tracking-wide text-gray-500 mb-2">Axis ledger</div>
        <div className="space-y-1.5">
          {Object.entries(axes).map(([key, a]) => {
            const q = axisQuality(a)
            const color = AXIS_COLORS[q]
            return (
              <div key={key} className="flex items-center gap-3 text-sm">
                <div className="w-2 h-2 rounded-sm flex-shrink-0" style={{ background: color }} />
                <div className="w-32 text-gray-300 capitalize flex-shrink-0">{key.replace(/_/g, ' ')}</div>
                <div className="w-24 font-mono text-gray-400 flex-shrink-0">{a.value}</div>
                <div className="w-20 font-mono flex-shrink-0" style={{ color }}>
                  {q === 'discounted' ? <span className="line-through">{(a.bits || 0).toFixed(2)}</span> : `${Number(a.bits || 0).toFixed(2)} b`}
                </div>
                <div className="flex-1 text-[11px] text-gray-500">
                  {q === 'discounted' && <span title="Governor-2: correlated, counted once via the other axis.">counted via {a.correlated_with}</span>}
                  {q === 'coarse' && <span title="v0 estimate — full per-name frequency is a later refinement.">coarse estimate</span>}
                  {q === 'measured' && a.p != null && <span>prevalence {Number(a.p) < 0.001 ? Number(a.p).toExponential(1) : Number(a.p).toFixed(3)}</span>}
                </div>
              </div>
            )
          })}
        </div>
      </div>

      {/* Not yet measured — the honesty signature */}
      {unknown.length > 0 && (
        <div className="border border-[#1e1e2e] rounded p-3 bg-[#0d0d14]">
          <div className="text-xs uppercase tracking-wide text-gray-500 mb-2">Not yet measured</div>
          <div className="flex flex-wrap gap-2">
            {unknown.map(u => (
              <span key={u} className="text-[11px] font-mono px-2 py-0.5 rounded border border-[#2a2a3e] text-gray-500"
                title="No reliable prior available — contributes 0 bits rather than a guess.">
                {u.replace(/_/g, ' ')}
              </span>
            ))}
          </div>
          <div className="text-[11px] text-gray-600 mt-2">
            These contribute <span className="font-mono">0 bits</span> — disclosed, not guessed. Resolving them would narrow further.
          </div>
        </div>
      )}

      {/* Sovereignty line */}
      <div className="border-l-2 border-[#00ff88] pl-3 py-1 text-sm text-gray-300">
        The open web has resolved <span className="font-mono text-[#3388ff]">{bits.toFixed(1)}</span> of your {unique} identity bits — {eb.verdict}.
        <div className="text-gray-500 text-xs mt-1">This is your ledger — returned to you, not held over you.</div>
      </div>
    </div>
  )
}
