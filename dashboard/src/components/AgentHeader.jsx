// S293 — agent-native detail header. Replaces the human ProfileHeader (avatar /
// "Unknown identity" / exposure/threat/breaches) for workspace_kind === 'agent'.
// WBA (agent_declared): operator / purpose / signature_agent / Ed25519 keys.
// Known bot (agent_known): operator / UA pattern / example instance / tags.
// Graceful: fields absent (e.g. Google has no purpose/signature_agent) are hidden.
const GREEN = '#00ff88'

function Glyph() {
  return (
    <div className="w-14 h-14 rounded-2xl bg-[#0f1420] border border-[#1e2a3a] flex items-center justify-center shrink-0">
      <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke={GREEN} strokeWidth="1.5">
        <rect x="4" y="8" width="16" height="11" rx="2" /><path d="M12 8V4M9 13h.01M15 13h.01M8 19v2M16 19v2" />
      </svg>
    </div>
  )
}

function Stat({ label, value, accent }) {
  return (
    <div>
      <div className="text-[11px] uppercase tracking-wide text-gray-500">{label}</div>
      <div className="text-lg font-mono mt-1" style={accent ? { color: GREEN } : undefined}>{value}</div>
    </div>
  )
}

function Chip({ children, tone = 'default' }) {
  const cls = tone === 'green'
    ? 'border-[#1e3a2a] text-[#00ff88] bg-[#0c1a12]'
    : 'border-[#1e2a3a] text-gray-300 bg-[#0f1420]'
  return <span className={`text-xs font-mono px-2 py-0.5 rounded border ${cls}`}>{children}</span>
}

export default function AgentHeader({ target, findings }) {
  const f = (findings || []).find(x => x.category === 'agent_declared' || x.category === 'agent_known') || {}
  const d = f.data || {}
  const pd = target.profile_data || {}
  const declared = f.category === 'agent_declared' || pd.source === 'wba'

  // WBA
  const keys = Array.isArray(d.keys) ? d.keys : []
  const purpose = d.purpose
  const sigAgent = d.signature_agent
  const algs = [...new Set(keys.map(k => k.crv).filter(Boolean))]
  // crawler-UA
  const pattern = d.pattern || pd.pattern
  const operatorUrl = d.url || pd.operator_url
  const instances = Array.isArray(d.instances) ? d.instances : []
  const tags = d.tags || pd.tags || []

  return (
    <div className="rounded-2xl border border-[#1e1e2e] bg-[#0b0e16] p-6">
      {/* identity row */}
      <div className="flex items-center gap-4 mb-5">
        <Glyph />
        <div className="min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <Chip tone={declared ? 'green' : 'default'}>
              {declared ? 'WBA · signed agent' : 'Known bot · UA-declared'}
            </Chip>
            {purpose && <Chip>purpose: {purpose}</Chip>}
          </div>
          <div className="text-lg font-mono text-white mt-1.5 truncate">{target.email}</div>
          {sigAgent && <div className="text-xs font-mono text-gray-400 truncate">{sigAgent}</div>}
          {!declared && operatorUrl && (
            <a href={operatorUrl} target="_blank" rel="noreferrer" className="text-xs text-gray-400 hover:text-[#00ff88] truncate block">{operatorUrl}</a>
          )}
        </div>
      </div>

      {/* tier-specific detail */}
      {declared ? (
        <div className="space-y-2 mb-5">
          <div className="text-[11px] uppercase tracking-wide text-gray-500">Signing keys ({keys.length})</div>
          {keys.slice(0, 6).map((k, i) => (
            <div key={i} className="text-xs font-mono text-gray-300 truncate">
              <span style={{ color: GREEN }}>{k.crv || k.kty}</span> · kid {k.kid}
              {k.exp && <span className="text-gray-500"> · exp {new Date((k.exp > 1e12 ? k.exp : k.exp * 1000)).toISOString().slice(0, 10)}</span>}
            </div>
          ))}
        </div>
      ) : (
        <div className="space-y-2 mb-5">
          <div><span className="text-[11px] uppercase tracking-wide text-gray-500">UA pattern</span>
            <div className="text-xs font-mono text-gray-300 break-all mt-0.5">{pattern}</div></div>
          {instances[0] && <div><span className="text-[11px] uppercase tracking-wide text-gray-500">Example instance</span>
            <div className="text-xs font-mono text-gray-400 break-all mt-0.5 line-clamp-2">{instances[0]}</div></div>}
          {tags.length > 0 && <div className="flex gap-1.5 flex-wrap pt-1">{tags.map((t, i) => <Chip key={i}>{t}</Chip>)}</div>}
        </div>
      )}

      {/* agent-native metrics (replace exposure/threat/breaches) */}
      <div className="grid grid-cols-3 gap-4 pt-4 border-t border-[#1e1e2e]">
        <Stat label="Provenance" value={declared ? 'Verifiable' : 'Self-declared'} accent={declared} />
        {declared
          ? <Stat label="Ed25519 keys" value={keys.length} />
          : <Stat label="UA instances" value={instances.length} />}
        {declared
          ? <Stat label="Algorithms" value={algs.join(', ') || '—'} />
          : <Stat label="Tags" value={tags.length} />}
      </div>
    </div>
  )
}
