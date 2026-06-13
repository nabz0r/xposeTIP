import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { getAgentNetwork } from '../lib/api'

// S295b — corpus-level agent network: AI agents clustered by operator ASN (the Place
// axis). Deterministic home-made SVG layout, zero dep. Reads the agent_network findings.

const FILL = { shared: '#185FA5', own: '#0F6E56', foreign: '#993C1D', host: '#5F5E5A' }
const CAT_LABEL = {
  shared: 'shared CDN', own: 'own ASN / hyperscaler', foreign: 'foreign network', host: '3rd-party host',
}

function category(asname = '') {
  const a = (asname || '').toLowerCase()
  if (a.includes('cloudflare') || a.includes('fastly') || a.includes('akamai')) return 'shared'
  if (a.includes('china') || a.includes('chinanet') || a.includes('tencent') || a.includes('alibaba')) return 'foreign'
  if (a.includes('hurricane') || a.includes('ovh') || a.includes('hetzner') || a.includes('digitalocean')) return 'host'
  return 'own'
}

function groupByAsn(nodes) {
  const m = new Map()
  for (const n of nodes) {
    const key = n.asn || 'unknown'
    if (!m.has(key)) m.set(key, { asn: n.asn, asname: n.asname || '', cat: category(n.asname), agents: [] })
    m.get(key).agents.push(n)
  }
  return [...m.values()].sort((a, b) => b.agents.length - a.agents.length)
}

const W = 720

export default function AgentNetwork() {
  const [nodes, setNodes] = useState(null)
  const [err, setErr] = useState(null)

  useEffect(() => {
    getAgentNetwork().then(r => setNodes(r.nodes || [])).catch(e => setErr(String(e)))
  }, [])

  if (err) return <div className="p-8 text-sm text-[#ff5577] font-mono">Failed to load: {err}</div>
  if (nodes === null) return <div className="p-8 text-sm text-gray-500 font-mono">Loading network…</div>

  const groups = groupByAsn(nodes)
  const cols = Math.max(1, Math.ceil(Math.sqrt(groups.length)))
  const rows = Math.ceil(groups.length / cols)
  const cellW = W / cols
  const cellH = 200
  const H = rows * cellH + 80

  // deterministic placement: hub at cell center, agents on a ring around it
  const placed = groups.map((g, gi) => {
    const col = gi % cols
    const row = Math.floor(gi / cols)
    const cx = col * cellW + cellW / 2
    const cy = row * cellH + cellH / 2 + 20
    const hubR = 18 + 5 * Math.sqrt(g.agents.length)
    const ringR = hubR + 38
    const agents = g.agents.map((a, i) => {
      const ang = (2 * Math.PI * i) / g.agents.length - Math.PI / 2
      return { ...a, x: cx + Math.cos(ang) * ringR, y: cy + Math.sin(ang) * ringR }
    })
    return { ...g, cx, cy, hubR, agents }
  })

  return (
    <div className="p-6">
      <div className="flex items-start justify-between mb-4">
        <div>
          <h1 className="text-xl font-semibold">Agent Network</h1>
          <p className="text-sm text-gray-500">AI agents clustered by operator ASN — the Place axis</p>
        </div>
        <div className="text-right">
          <div className="text-xs font-mono text-gray-400">{nodes.length} agents · {groups.length} networks</div>
          <Link to="/targets" className="text-xs text-gray-500 hover:text-[#00ff88]">← targets</Link>
        </div>
      </div>

      {nodes.length === 0 ? (
        <div className="rounded-2xl border border-[#1e1e2e] bg-[#0b0e16] p-10 text-center text-sm text-gray-500">
          No network data yet — run <span className="font-mono text-gray-400">scripts/resolve_ai_agent_network.py</span> to populate.
        </div>
      ) : (
        <div className="rounded-2xl border border-[#1e1e2e] bg-[#0b0e16] p-4 overflow-x-auto">
          <svg viewBox={`0 0 ${W} ${H}`} className="w-full h-auto" xmlns="http://www.w3.org/2000/svg">
            {/* edges first (under nodes) */}
            {placed.map(g => g.agents.map((a, i) => (
              <line key={`e-${g.asn}-${i}`} x1={g.cx} y1={g.cy} x2={a.x} y2={a.y}
                stroke="#1e2a3a" strokeWidth="1" />
            )))}
            {/* hubs */}
            {placed.map(g => (
              <g key={`h-${g.asn}`}>
                <circle cx={g.cx} cy={g.cy} r={g.hubR} fill={FILL[g.cat]} opacity="0.9" />
                <text x={g.cx} y={g.cy - 2} textAnchor="middle" fill="#fff" fontSize="11" fontFamily="monospace" fontWeight="bold">
                  {(g.asname || '').split(' ')[0].slice(0, 14)}
                </text>
                <text x={g.cx} y={g.cy + 11} textAnchor="middle" fill="#cfe" fontSize="9" fontFamily="monospace">
                  {(g.asn || '').split(' ')[0]}
                </text>
              </g>
            ))}
            {/* agents */}
            {placed.map(g => g.agents.map((a, i) => (
              <g key={`a-${g.asn}-${i}`}>
                <circle cx={a.x} cy={a.y} r="13" fill="#0f1420" stroke={a.signed ? '#639922' : '#2a3344'} strokeWidth={a.signed ? '2' : '1'} />
                <text x={a.x} y={a.y + 26} textAnchor="middle" fill="#9fb0c3" fontSize="10" fontFamily="monospace">
                  {(a.operator || '').replace(/\\\/$/, '').slice(0, 16)}
                </text>
              </g>
            )))}
          </svg>

          {/* legend */}
          <div className="flex gap-4 flex-wrap mt-3 pt-3 border-t border-[#1e1e2e] text-[11px] font-mono text-gray-400">
            {Object.entries(CAT_LABEL).map(([k, label]) => (
              <span key={k} className="flex items-center gap-1.5">
                <span className="w-3 h-3 rounded-full inline-block" style={{ background: FILL[k] }} />{label}
              </span>
            ))}
            <span className="flex items-center gap-1.5">
              <span className="w-3 h-3 rounded-full inline-block border-2 border-[#639922]" />WBA signed
            </span>
          </div>
        </div>
      )}
    </div>
  )
}
