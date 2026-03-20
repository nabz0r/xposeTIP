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
}

const nodeRadius = {
  email: 18,
  social_url: 12,
  breach: 14,
  domain: 12,
  username: 12,
  ip: 10,
  paste: 10,
}

export default function IdentityGraph({ data }) {
  const svgRef = useRef()
  const containerRef = useRef()
  const [selected, setSelected] = useState(null)

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
      .force('collision', d3.forceCollide().radius(d => (nodeRadius[d.type] || 10) + 5))

    // Edges
    const link = g.append('g')
      .selectAll('line')
      .data(links)
      .join('line')
      .attr('stroke', '#1e1e2e')
      .attr('stroke-width', d => Math.max(1, d.confidence * 2.5))
      .attr('stroke-opacity', 0.6)

    // Edge labels
    const linkLabel = g.append('g')
      .selectAll('text')
      .data(links)
      .join('text')
      .attr('font-size', 8)
      .attr('fill', '#666688')
      .attr('text-anchor', 'middle')
      .text(d => d.type.replace(/_/g, ' '))

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
      .attr('r', d => nodeRadius[d.type] || 10)
      .attr('fill', d => (nodeColors[d.type] || '#666688') + '33')
      .attr('stroke', d => nodeColors[d.type] || '#666688')
      .attr('stroke-width', 2)
      .attr('filter', d => d.type === 'email' ? 'url(#glow)' : null)

    node.append('text')
      .attr('dy', d => (nodeRadius[d.type] || 10) + 14)
      .attr('text-anchor', 'middle')
      .attr('font-size', 10)
      .attr('fill', '#888')
      .attr('font-family', 'JetBrains Mono, monospace')
      .text(d => {
        const v = d.value
        return v.length > 20 ? v.slice(0, 18) + '…' : v
      })

    // Type icon text inside node
    node.append('text')
      .attr('dy', 4)
      .attr('text-anchor', 'middle')
      .attr('font-size', d => (nodeRadius[d.type] || 10) * 0.8)
      .attr('fill', d => nodeColors[d.type] || '#666688')
      .text(d => {
        const icons = { email: '@', social_url: '🔗', breach: '⚠', domain: '🌐', username: '👤', ip: '📍', paste: '📋' }
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

    return () => simulation.stop()
  }, [data])

  if (!data || !data.nodes.length) {
    return (
      <div className="flex items-center justify-center h-64 text-gray-500">
        No identity graph data yet. Run a scan to build the graph.
      </div>
    )
  }

  return (
    <div className="relative" ref={containerRef} style={{ minHeight: 500 }}>
      <svg ref={svgRef} className="w-full" style={{ minHeight: 500, background: '#0a0a0f', borderRadius: 12 }} />

      {/* Legend */}
      <div className="absolute top-3 left-3 bg-[#12121a]/90 border border-[#1e1e2e] rounded-lg p-3 text-xs space-y-1">
        {Object.entries(nodeColors).map(([type, color]) => (
          <div key={type} className="flex items-center gap-2">
            <span className="w-3 h-3 rounded-full" style={{ backgroundColor: color }} />
            <span className="text-gray-400">{type.replace(/_/g, ' ')}</span>
          </div>
        ))}
      </div>

      {/* Stats */}
      <div className="absolute top-3 right-3 bg-[#12121a]/90 border border-[#1e1e2e] rounded-lg p-3 text-xs text-gray-400">
        <div>{data.stats.total_nodes} nodes</div>
        <div>{data.stats.total_edges} edges</div>
      </div>

      {/* Detail panel */}
      {selected && (
        <div className="absolute bottom-3 left-3 right-3 bg-[#12121a] border border-[#1e1e2e] rounded-lg p-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <span className="w-3 h-3 rounded-full" style={{ backgroundColor: nodeColors[selected.type] || '#666688' }} />
              <span className="font-mono text-sm">{selected.value}</span>
            </div>
            <button onClick={() => setSelected(null)} className="text-gray-500 hover:text-white text-sm">✕</button>
          </div>
          <div className="mt-2 grid grid-cols-3 gap-4 text-xs text-gray-400">
            <div><span className="text-gray-500">Type:</span> {selected.type}</div>
            <div><span className="text-gray-500">Platform:</span> {selected.platform || '-'}</div>
            <div><span className="text-gray-500">Module:</span> {selected.source_module || '-'}</div>
            <div><span className="text-gray-500">Confidence:</span> {(selected.confidence * 100).toFixed(0)}%</div>
          </div>
        </div>
      )}
    </div>
  )
}
