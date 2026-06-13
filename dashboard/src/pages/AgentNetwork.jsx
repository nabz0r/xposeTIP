import { useEffect, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import * as d3 from 'd3'
import { getAgentNetwork } from '../lib/api'

// S295c — corpus-level agent network: AI agents clustered by operator ASN (the Place
// axis). d3-force layout (modeled on IdentityGraph.jsx) — Cloudflare emerges as the
// natural super-hub, zero collision, nodes carry the bot name (not the repeated domain).
// Same endpoint / same data as S295b — purely a render swap (grid → force). Zero dep.

const FILL = { shared: '#185FA5', own: '#0F6E56', foreign: '#993C1D', host: '#5F5E5A' }
const CAT_LABEL = {
  shared: 'shared CDN', own: 'own ASN / hyperscaler', foreign: 'foreign network', host: '3rd-party host',
}

// crawler-UA findings carry email='ua:GPTBot' → 'GPTBot' ; WBA/curated carry the operator domain
const botLabel = (email = '') => (email.startsWith('ua:') ? email.slice(3) : email)

function category(asname = '') {
  const a = (asname || '').toLowerCase()
  if (a.includes('cloudflare') || a.includes('fastly') || a.includes('akamai')) return 'shared'
  if (a.includes('china') || a.includes('chinanet') || a.includes('tencent') || a.includes('alibaba')) return 'foreign'
  if (a.includes('hurricane') || a.includes('ovh') || a.includes('hetzner') || a.includes('digitalocean')) return 'host'
  return 'own'
}

const hubR = (count) => 16 + 5 * Math.sqrt(count)

export default function AgentNetwork() {
  const [data, setData] = useState(null)
  const [err, setErr] = useState(null)
  const svgRef = useRef()
  const containerRef = useRef()

  useEffect(() => {
    getAgentNetwork().then(r => setData(r.nodes || [])).catch(e => setErr(String(e)))
  }, [])

  useEffect(() => {
    if (!data || !data.length) return

    const container = containerRef.current
    const width = container.clientWidth
    const height = 620

    // build graph: one hub per ASN, one node per agent, link agent→hub
    const hubs = new Map()
    data.forEach(n => {
      const key = n.asn || 'unknown'
      if (!hubs.has(key)) {
        hubs.set(key, {
          id: `hub:${key}`, kind: 'hub', asn: n.asn, asname: n.asname || '',
          cat: category(n.asname), count: 0,
        })
      }
      hubs.get(key).count++
    })
    const hubNodes = [...hubs.values()]
    const agentNodes = data.map((n, i) => ({
      id: `a:${i}`, kind: 'agent', label: botLabel(n.email), operator: n.operator,
      cat: category(n.asname), signed: n.signed, hub: `hub:${n.asn || 'unknown'}`,
    }))
    const graphNodes = [...hubNodes, ...agentNodes]
    const links = agentNodes.map(a => ({ source: a.id, target: a.hub }))

    d3.select(svgRef.current).selectAll('*').remove()
    const svg = d3.select(svgRef.current).attr('width', width).attr('height', height)
    const g = svg.append('g')

    const zoom = d3.zoom().scaleExtent([0.3, 4]).on('zoom', (e) => g.attr('transform', e.transform))
    svg.call(zoom)

    // The 11 ASN clusters are disconnected components (agents link only to their own
    // hub; hubs never interlink). forceCenter alone only pins the centroid, so strong
    // charge lets the components fly far apart → a tiny auto-fit scale. Mild forceX/forceY
    // gravity gathers every cluster toward center; collide + charge still separate them
    // locally, so Cloudflare (most agents) still settles biggest/central.
    const sim = d3.forceSimulation(graphNodes)
      .force('link', d3.forceLink(links).id(d => d.id).distance(44).strength(0.8))
      .force('charge', d3.forceManyBody().strength(d => d.kind === 'hub' ? -300 : -80))
      .force('x', d3.forceX(width / 2).strength(0.07))
      .force('y', d3.forceY(height / 2).strength(0.07))
      .force('collide', d3.forceCollide().radius(d => (d.kind === 'hub' ? hubR(d.count) : 9) + 16))

    // links (under nodes)
    const link = g.append('g').selectAll('line')
      .data(links).join('line')
      .attr('stroke', '#1e2a3a').attr('stroke-width', 1).attr('stroke-opacity', 0.5)

    const node = g.append('g').selectAll('g')
      .data(graphNodes).join('g')
      .call(d3.drag()
        .on('start', (e, d) => { if (!e.active) sim.alphaTarget(0.3).restart(); d.fx = d.x; d.fy = d.y })
        .on('drag', (e, d) => { d.fx = e.x; d.fy = e.y })
        .on('end', (e, d) => { if (!e.active) sim.alphaTarget(0); d.fx = null; d.fy = null }))

    // signed ring (WBA) — drawn first so it sits behind the node body
    node.filter(d => d.signed).append('circle')
      .attr('r', d => (d.kind === 'hub' ? hubR(d.count) : 8) + 4)
      .attr('fill', 'none').attr('stroke', '#9bcc3a').attr('stroke-width', 2)

    // node body
    node.append('circle')
      .attr('r', d => (d.kind === 'hub' ? hubR(d.count) : 8))
      .attr('fill', d => (d.kind === 'hub' ? FILL[d.cat] : '#10151f'))
      .attr('fill-opacity', d => (d.kind === 'hub' ? 0.9 : 1))
      .attr('stroke', d => FILL[d.cat])
      .attr('stroke-width', d => (d.kind === 'hub' ? 0 : 1.5))

    // hub label: asname (bold) + asn — centered inside the big circle
    const hub = node.filter(d => d.kind === 'hub')
    hub.append('text')
      .attr('text-anchor', 'middle').attr('dy', -2)
      .attr('fill', '#fff').attr('font-size', 11).attr('font-weight', 'bold')
      .attr('font-family', 'JetBrains Mono, monospace')
      .text(d => (d.asname || '').split(' ')[0].slice(0, 14))
    hub.append('text')
      .attr('text-anchor', 'middle').attr('dy', 11)
      .attr('fill', '#cfe').attr('font-size', 10)
      .attr('font-family', 'JetBrains Mono, monospace')
      .text(d => d.asn || '')

    // agent label: bot name below the dot
    node.filter(d => d.kind === 'agent').append('text')
      .attr('text-anchor', 'middle').attr('dy', 20)
      .attr('fill', '#9aa7bd').attr('font-size', 10)
      .attr('font-family', 'JetBrains Mono, monospace')
      .text(d => (d.label || '').slice(0, 18))

    sim.on('tick', () => {
      link
        .attr('x1', d => d.source.x).attr('y1', d => d.source.y)
        .attr('x2', d => d.target.x).attr('y2', d => d.target.y)
      node.attr('transform', d => `translate(${d.x},${d.y})`)
    })

    // auto zoom-to-fit once the layout stabilizes — the 11 clusters spread wider than
    // the fixed canvas, so without this only a couple of hubs land in view (IdentityGraph
    // pattern). Pan/zoom stays available afterwards.
    sim.on('end', () => {
      let minX = Infinity, maxX = -Infinity, minY = Infinity, maxY = -Infinity
      graphNodes.forEach(d => {
        if (d.x < minX) minX = d.x; if (d.x > maxX) maxX = d.x
        if (d.y < minY) minY = d.y; if (d.y > maxY) maxY = d.y
      })
      const pad = 70
      const gw = maxX - minX + pad * 2, gh = maxY - minY + pad * 2
      if (gw > 0 && gh > 0) {
        const scale = Math.min(width / gw, height / gh, 1.6)
        const cx = (minX + maxX) / 2, cy = (minY + maxY) / 2
        const t = d3.zoomIdentity.translate(width / 2, height / 2).scale(scale).translate(-cx, -cy)
        svg.transition().duration(600).call(zoom.transform, t)
      }
    })

    return () => sim.stop()
  }, [data])

  if (err) return <div className="p-8 text-sm text-[#ff5577] font-mono">Failed to load: {err}</div>
  if (data === null) return <div className="p-8 text-sm text-gray-500 font-mono">Loading network…</div>

  const hubCount = new Set(data.map(n => n.asn || 'unknown')).size

  return (
    <div className="p-6">
      <div className="flex items-start justify-between mb-4">
        <div>
          <h1 className="text-xl font-semibold">Agent Network</h1>
          <p className="text-sm text-gray-500">AI agents clustered by operator ASN — the Place axis</p>
        </div>
        <div className="text-right">
          <div className="text-xs font-mono text-gray-400">{data.length} agents · {hubCount} networks</div>
          <Link to="/targets" className="text-xs text-gray-500 hover:text-[#00ff88]">← targets</Link>
        </div>
      </div>

      {data.length === 0 ? (
        <div className="rounded-2xl border border-[#1e1e2e] bg-[#0b0e16] p-10 text-center text-sm text-gray-500">
          No network data yet — run <span className="font-mono text-gray-400">scripts/resolve_ai_agent_network.py</span> to populate.
        </div>
      ) : (
        <div className="rounded-2xl border border-[#1e1e2e] bg-[#0b0e16] p-4">
          <div ref={containerRef} className="relative">
            <svg ref={svgRef} className="w-full" style={{ background: '#0b0e16', borderRadius: 8 }} />
          </div>
          <div className="text-[10px] text-gray-600 mt-1 text-center">Scroll to zoom · Drag to pan · Drag a node to reposition</div>

          {/* legend */}
          <div className="flex gap-4 flex-wrap mt-3 pt-3 border-t border-[#1e1e2e] text-[11px] font-mono text-gray-400">
            {Object.entries(CAT_LABEL).map(([k, label]) => (
              <span key={k} className="flex items-center gap-1.5">
                <span className="w-3 h-3 rounded-full inline-block" style={{ background: FILL[k] }} />{label}
              </span>
            ))}
            <span className="flex items-center gap-1.5">
              <span className="w-3 h-3 rounded-full inline-block border-2 border-[#9bcc3a]" />WBA signed
            </span>
          </div>
        </div>
      )}
    </div>
  )
}
