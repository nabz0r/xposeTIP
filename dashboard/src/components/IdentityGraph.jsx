import { useEffect, useRef, useState } from 'react'
import * as d3 from 'd3'

const nodeColors = {
  email: '#00ff88',
  social_url: '#3388ff',
  social_account: '#3388ff',
  breach: '#ff2244',
  domain: '#aa55ff',
  username: '#ff8800',
  ip: '#ffcc00',
  paste: '#ff4466',
  name: '#00ddcc',
  location: '#cc88ff',
}

const CLUSTER_COLORS = [
  '#00ff88', '#3388ff', '#ff8800', '#aa55ff', '#ffcc00', '#ff4466', '#00ddcc',
]

const PERSONA_COLORS = CLUSTER_COLORS

export default function IdentityGraph({ data, personas = [] }) {
  const svgRef = useRef()
  const containerRef = useRef()
  const [selected, setSelected] = useState(null)

  // Compute edge counts for dynamic sizing
  const edgeCounts = {}
  if (data?.edges) {
    data.edges.forEach(e => {
      edgeCounts[e.source] = (edgeCounts[e.source] || 0) + 1
      edgeCounts[e.dest] = (edgeCounts[e.dest] || 0) + 1
    })
  }

  const getNodeColor = (node) => {
    if (node.type === 'email') return '#ffffff'  // Email = white anchor
    if (node.type === 'breach') return '#ff2244'
    // Use graph cluster_id for coloring (Markov chain integration)
    if (node.cluster_id !== undefined && node.cluster_id !== null) {
      return CLUSTER_COLORS[node.cluster_id % CLUSTER_COLORS.length]
    }
    // Fallback to persona coloring
    const personaId = node.metadata?.persona
    if (personaId) {
      const idx = parseInt(personaId.replace('persona_', '')) || 0
      return PERSONA_COLORS[idx % PERSONA_COLORS.length]
    }
    return nodeColors[node.type] || '#666688'
  }

  const getDynamicRadius = (node) => {
    // Size proportional to PageRank confidence
    const conf = node.confidence || 0.5
    const base = 6 + conf * 18  // 6px at 0 → 24px at 1.0
    const edges = edgeCounts[node.id] || 0
    return Math.max(base, 8) + Math.min(edges * 2, 10)
  }

  // Get connected nodes for detail panel
  const getConnectedNodes = (nodeId) => {
    if (!data?.edges) return []
    const connected = []
    data.edges.forEach(e => {
      if (e.source === nodeId || (typeof e.source === 'object' && e.source?.id === nodeId)) {
        const targetId = typeof e.dest === 'object' ? e.dest.id : e.dest
        const targetNode = data.nodes.find(n => n.id === targetId)
        if (targetNode) connected.push({ node: targetNode, type: e.type })
      }
      if (e.dest === nodeId || (typeof e.dest === 'object' && e.dest?.id === nodeId)) {
        const sourceId = typeof e.source === 'object' ? e.source.id : e.source
        const sourceNode = data.nodes.find(n => n.id === sourceId)
        if (sourceNode) connected.push({ node: sourceNode, type: e.type })
      }
    })
    return connected
  }

  useEffect(() => {
    if (!data || !data.nodes.length) return

    const container = containerRef.current
    const width = container.clientWidth
    const height = Math.max(500, container.clientHeight)

    d3.select(svgRef.current).selectAll('*').remove()

    const svg = d3.select(svgRef.current)
      .attr('width', width)
      .attr('height', height)

    const g = svg.append('g')

    // Zoom
    const zoom = d3.zoom()
      .scaleExtent([0.3, 4])
      .on('zoom', (event) => g.attr('transform', event.transform))
    svg.call(zoom)

    // Map edges source/dest to node ids
    const nodeMap = new Map(data.nodes.map(n => [n.id, n]))
    const links = data.edges
      .filter(e => nodeMap.has(e.source) && nodeMap.has(e.dest))
      .map(e => ({ ...e, source: e.source, target: e.dest }))

    const simulation = d3.forceSimulation(data.nodes)
      .force('link', d3.forceLink(links).id(d => d.id).distance(100))
      .force('charge', d3.forceManyBody().strength(-300))
      .force('center', d3.forceCenter(width / 2, height / 2))
      .force('collision', d3.forceCollide().radius(d => getDynamicRadius(d) + 5))

    // Edges — width by transition probability (Markov chain weight)
    const link = g.append('g')
      .selectAll('line')
      .data(links)
      .join('line')
      .attr('stroke', '#1e1e2e')
      .attr('stroke-width', d => {
        const prob = d.transition_probability || d.confidence || 0.1
        return 0.5 + prob * 4  // 0.5px at 0 → 4.5px at 1.0
      })
      .attr('stroke-opacity', 0.6)

    // Edge labels — hidden by default, shown on hover
    const linkLabel = g.append('g')
      .selectAll('text')
      .data(links)
      .join('text')
      .attr('font-size', 8)
      .attr('fill', '#666688')
      .attr('text-anchor', 'middle')
      .attr('opacity', 0)
      .text(d => d.type.replace(/_/g, ' '))

    // Show edge labels on hover
    link.on('mouseover', function(event, d) {
      linkLabel.filter(l => l === d).attr('opacity', 1)
      d3.select(this).attr('stroke-opacity', 1).attr('stroke', '#555')
    })
    .on('mouseout', function(event, d) {
      linkLabel.filter(l => l === d).attr('opacity', 0)
      d3.select(this).attr('stroke-opacity', 0.6).attr('stroke', '#1e1e2e')
    })

    // Nodes
    const node = g.append('g')
      .selectAll('g')
      .data(data.nodes)
      .join('g')
      .call(d3.drag()
        .on('start', (event, d) => {
          if (!event.active) simulation.alphaTarget(0.3).restart()
          d.fx = d.x; d.fy = d.y
        })
        .on('drag', (event, d) => { d.fx = event.x; d.fy = event.y })
        .on('end', (event, d) => {
          if (!event.active) simulation.alphaTarget(0)
          d.fx = null; d.fy = null
        })
      )

    // Glow filter for center node
    const defs = svg.append('defs')
    const filter = defs.append('filter').attr('id', 'glow')
    filter.append('feGaussianBlur').attr('stdDeviation', '3').attr('result', 'coloredBlur')
    const feMerge = filter.append('feMerge')
    feMerge.append('feMergeNode').attr('in', 'coloredBlur')
    feMerge.append('feMergeNode').attr('in', 'SourceGraphic')

    node.append('circle')
      .attr('r', d => getDynamicRadius(d))
      .attr('fill', d => getNodeColor(d) + '33')
      .attr('stroke', d => getNodeColor(d))
      .attr('stroke-width', 2)
      .attr('filter', d => d.type === 'email' ? 'url(#glow)' : null)

    node.append('text')
      .attr('dy', d => getDynamicRadius(d) + 14)
      .attr('text-anchor', 'middle')
      .attr('font-size', d => {
        const edges = edgeCounts[d.id] || 0
        return edges >= 5 ? 12 : edges >= 2 ? 11 : 10
      })
      .attr('fill', '#888')
      .attr('font-family', 'JetBrains Mono, monospace')
      .attr('opacity', d => {
        const edges = edgeCounts[d.id] || 0
        if (edges >= 3) return 1
        if ((d.confidence || 0) > 0.3) return 0.8
        return 0.4
      })
      .text(d => {
        const v = d.value
        return v.length > 20 ? v.slice(0, 18) + '…' : v
      })

    // Type icon text inside node
    node.append('text')
      .attr('dy', 4)
      .attr('text-anchor', 'middle')
      .attr('font-size', d => getDynamicRadius(d) * 0.7)
      .attr('fill', d => getNodeColor(d))
      .text(d => {
        const icons = { email: '@', social_url: '🔗', breach: '⚠', domain: '🌐', username: '👤', ip: '📍', paste: '📋', name: '🏷', location: '📍' }
        return icons[d.type] || '•'
      })

    // Hover highlight
    node.on('mouseover', function (event, d) {
      const connectedIds = new Set()
      links.forEach(l => {
        const src = typeof l.source === 'object' ? l.source.id : l.source
        const tgt = typeof l.target === 'object' ? l.target.id : l.target
        if (src === d.id) connectedIds.add(tgt)
        if (tgt === d.id) connectedIds.add(src)
      })
      connectedIds.add(d.id)
      node.style('opacity', n => connectedIds.has(n.id) ? 1 : 0.2)
      link.style('opacity', l => {
        const src = typeof l.source === 'object' ? l.source.id : l.source
        const tgt = typeof l.target === 'object' ? l.target.id : l.target
        return src === d.id || tgt === d.id ? 1 : 0.05
      })
    })
    .on('mouseout', () => {
      node.style('opacity', 1)
      link.style('opacity', 0.6)
    })
    .on('click', (event, d) => setSelected(d))

    simulation.on('tick', () => {
      link
        .attr('x1', d => d.source.x).attr('y1', d => d.source.y)
        .attr('x2', d => d.target.x).attr('y2', d => d.target.y)
      linkLabel
        .attr('x', d => (d.source.x + d.target.x) / 2)
        .attr('y', d => (d.source.y + d.target.y) / 2)
      node.attr('transform', d => `translate(${d.x},${d.y})`)
    })

    // Auto zoom-to-fit after simulation stabilizes
    simulation.on('end', () => {
      let minX = Infinity, maxX = -Infinity, minY = Infinity, maxY = -Infinity
      data.nodes.forEach(d => {
        if (d.x < minX) minX = d.x
        if (d.x > maxX) maxX = d.x
        if (d.y < minY) minY = d.y
        if (d.y > maxY) maxY = d.y
      })

      const padding = 60
      const graphWidth = maxX - minX + padding * 2
      const graphHeight = maxY - minY + padding * 2

      if (graphWidth > 0 && graphHeight > 0) {
        const scale = Math.min(
          width / graphWidth,
          height / graphHeight,
          2.0
        ) * 0.9

        const centerX = (minX + maxX) / 2
        const centerY = (minY + maxY) / 2

        const transform = d3.zoomIdentity
          .translate(width / 2, height / 2)
          .scale(scale)
          .translate(-centerX, -centerY)

        svg.transition()
          .duration(750)
          .call(zoom.transform, transform)
      }
    })

    return () => simulation.stop()
  }, [data])

  if (!data || !data.nodes.length) {
    return (
      <div className="flex items-center justify-center h-64 text-gray-500">
        No identity graph data yet. Run a scan to build the graph.
      </div>
    )
  }

  const connectedNodes = selected ? getConnectedNodes(selected.id) : []
  const selectedPersona = selected?.metadata?.persona
  const personaLabel = selectedPersona ? personas.find(p => p.id === selectedPersona)?.label : null

  return (
    <div className="relative" ref={containerRef} style={{ minHeight: 500 }}>
      <svg ref={svgRef} className="w-full" style={{ minHeight: 500, background: '#0a0a0f', borderRadius: 12 }} />
      <div className="text-[10px] text-gray-600 mt-1 text-center">Scroll to zoom · Drag to pan · Click node for details</div>

      {/* Type Legend */}
      <div className="absolute top-3 left-3 bg-[#12121a]/90 border border-[#1e1e2e] rounded-lg p-3 text-xs space-y-1">
        {Object.entries(nodeColors).map(([type, color]) => (
          <div key={type} className="flex items-center gap-2">
            <span className="w-3 h-3 rounded-full" style={{ backgroundColor: color }} />
            <span className="text-gray-400">{type.replace(/_/g, ' ')}</span>
          </div>
        ))}
      </div>

      {/* Persona Legend */}
      {personas.length > 0 && (
        <div className="absolute top-3 left-3 mt-[200px] bg-[#12121a]/90 border border-[#1e1e2e] rounded-lg p-3 text-xs space-y-1">
          <div className="text-gray-500 font-semibold mb-1">Personas</div>
          {personas.map((p, i) => (
            <div key={p.id} className="flex items-center gap-2">
              <span className="w-3 h-3 rounded-full" style={{ backgroundColor: PERSONA_COLORS[i % PERSONA_COLORS.length] }} />
              <span className="text-gray-400">@{p.label}</span>
              <span className="text-gray-600">({p.accounts_count})</span>
            </div>
          ))}
        </div>
      )}

      {/* Stats */}
      <div className="absolute top-3 right-3 bg-[#12121a]/90 border border-[#1e1e2e] rounded-lg p-3 text-xs text-gray-400 space-y-0.5">
        <div>{data.stats.total_nodes} nodes</div>
        <div>{data.stats.total_edges} edges</div>
        {data.stats.clusters > 0 && (
          <div className="pt-1 border-t border-[#1e1e2e] mt-1">{data.stats.clusters} cluster{data.stats.clusters !== 1 ? 's' : ''}</div>
        )}
        {data.graph_clusters?.length > 0 && data.graph_clusters.map((c, i) => (
          <div key={c.id} className="flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full" style={{ backgroundColor: CLUSTER_COLORS[i % CLUSTER_COLORS.length] }} />
            <span>{c.node_count} nodes</span>
            <span className="text-gray-600">{(c.confidence * 100).toFixed(0)}%</span>
          </div>
        ))}
      </div>

      {/* Detail panel */}
      {selected && (
        <div className="absolute bottom-3 left-3 right-3 bg-[#12121a] border border-[#1e1e2e] rounded-lg p-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <span className="w-3 h-3 rounded-full" style={{ backgroundColor: getNodeColor(selected) }} />
              <span className="font-mono text-sm">{selected.value}</span>
              {personaLabel && (
                <span className="text-[10px] font-mono px-1.5 py-0.5 rounded-full bg-[#3388ff]/10 text-[#3388ff]">
                  @{personaLabel} persona
                </span>
              )}
            </div>
            <button onClick={() => setSelected(null)} className="text-gray-500 hover:text-white text-sm">✕</button>
          </div>
          <div className="mt-2 grid grid-cols-5 gap-4 text-xs text-gray-400">
            <div><span className="text-gray-500">Type:</span> {selected.type}</div>
            <div><span className="text-gray-500">Platform:</span> {selected.platform || '-'}</div>
            <div><span className="text-gray-500">Module:</span> {selected.source_module || '-'}</div>
            <div>
              <span className="text-gray-500">Confidence:</span>{' '}
              <span style={{ color: (selected.confidence || 0) > 0.6 ? '#00ff88' : (selected.confidence || 0) > 0.3 ? '#ffcc00' : '#ff8800' }}>
                {((selected.confidence || 0) * 100).toFixed(0)}%
              </span>
            </div>
            {selected.cluster_id !== undefined && selected.cluster_id !== null && (
              <div>
                <span className="text-gray-500">Cluster:</span>{' '}
                <span style={{ color: CLUSTER_COLORS[selected.cluster_id % CLUSTER_COLORS.length] }}>
                  #{selected.cluster_id}
                </span>
              </div>
            )}
          </div>
          {connectedNodes.length > 0 && (
            <div className="mt-2 pt-2 border-t border-[#1e1e2e]">
              <div className="text-[10px] text-gray-500 mb-1">Connected ({connectedNodes.length}):</div>
              <div className="flex flex-wrap gap-1.5">
                {connectedNodes.slice(0, 8).map((cn, i) => (
                  <span key={i} className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-[#1e1e2e] text-gray-400">
                    {cn.node.value.length > 20 ? cn.node.value.slice(0, 18) + '…' : cn.node.value}
                    <span className="text-gray-600 ml-1">({cn.type.replace(/_/g, ' ')})</span>
                  </span>
                ))}
                {connectedNodes.length > 8 && <span className="text-[10px] text-gray-500">+{connectedNodes.length - 8} more</span>}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
