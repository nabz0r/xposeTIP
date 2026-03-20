import { useEffect, useRef, useState } from 'react'
import * as d3 from 'd3'

// Simplified world GeoJSON inline — just country outlines
// We fetch the real one from a CDN at runtime
const GEO_URL = 'https://cdn.jsdelivr.net/npm/world-atlas@2/countries-110m.json'

export default function WorldHeatmap({ findings }) {
  const svgRef = useRef()
  const containerRef = useRef()
  const [tooltip, setTooltip] = useState(null)
  const [geoData, setGeoData] = useState(null)

  // Extract country counts from findings
  const countryCounts = {}
  for (const f of (findings || [])) {
    const cc = f.data?.country_code || f.data?.country
    if (cc) {
      const key = cc.length === 2 ? cc.toUpperCase() : cc
      countryCounts[key] = (countryCounts[key] || 0) + 1
    }
  }

  const hasData = Object.keys(countryCounts).length > 0

  useEffect(() => {
    // Fetch world topology
    fetch(GEO_URL)
      .then(r => r.json())
      .then(topology => {
        const feature = topojsonFeature(topology)
        setGeoData(feature)
      })
      .catch(() => {})
  }, [])

  useEffect(() => {
    if (!geoData) return

    const container = containerRef.current
    const width = container.clientWidth
    const height = 300

    d3.select(svgRef.current).selectAll('*').remove()

    const svg = d3.select(svgRef.current)
      .attr('width', width)
      .attr('height', height)

    const projection = d3.geoNaturalEarth1()
      .fitSize([width, height], geoData)

    const path = d3.geoPath().projection(projection)

    const maxCount = Math.max(1, ...Object.values(countryCounts))
    const colorScale = d3.scaleSequential(d3.interpolateGreens)
      .domain([0, maxCount])

    svg.append('g')
      .selectAll('path')
      .data(geoData.features)
      .join('path')
      .attr('d', path)
      .attr('fill', d => {
        const id = d.properties?.iso_a2 || d.id
        const count = countryCounts[id] || 0
        return count > 0 ? colorScale(count) : '#12121a'
      })
      .attr('stroke', '#1e1e2e')
      .attr('stroke-width', 0.5)
      .on('mouseover', (event, d) => {
        const id = d.properties?.iso_a2 || d.id
        const count = countryCounts[id] || 0
        const name = d.properties?.name || id
        if (count > 0) {
          setTooltip({ name, count, x: event.offsetX, y: event.offsetY })
        }
      })
      .on('mouseout', () => setTooltip(null))
  }, [geoData, countryCounts])

  return (
    <div className="bg-[#12121a] border border-[#1e1e2e] rounded-xl p-4" ref={containerRef}>
      <h3 className="text-sm font-semibold mb-3">Geographic Exposure</h3>
      {!hasData && (
        <div className="text-center py-6 text-gray-500 text-sm">
          Geographic exposure mapping requires the MaxMind GeoIP module.
          <br />
          <span className="text-xs text-gray-600">Configure your MaxMind license key in Settings &rarr; API Keys.</span>
        </div>
      )}
      <div className="relative">
        <svg ref={svgRef} className="w-full" style={{ minHeight: 300 }} />
        {tooltip && (
          <div className="absolute bg-[#0a0a0f] border border-[#1e1e2e] rounded-lg px-3 py-2 text-xs pointer-events-none"
            style={{ left: tooltip.x + 10, top: tooltip.y - 30 }}>
            <span className="text-white font-medium">{tooltip.name}</span>
            <span className="text-[#00ff88] ml-2">{tooltip.count} findings</span>
          </div>
        )}
      </div>
    </div>
  )
}

// Minimal topojson → geojson converter (avoids extra dep)
function topojsonFeature(topology) {
  const key = Object.keys(topology.objects)[0]
  const geojson = topology.objects[key]
  const arcs = topology.arcs

  function decodeArc(arcIndex) {
    const arc = arcs[arcIndex < 0 ? ~arcIndex : arcIndex]
    const coords = []
    let x = 0, y = 0
    for (const [dx, dy] of arc) {
      x += dx; y += dy
      coords.push([
        x * topology.transform.scale[0] + topology.transform.translate[0],
        y * topology.transform.scale[1] + topology.transform.translate[1],
      ])
    }
    if (arcIndex < 0) coords.reverse()
    return coords
  }

  function decodeRings(rings) {
    return rings.map(ring => {
      const coords = []
      for (const arcIdx of ring) {
        const decoded = decodeArc(arcIdx)
        coords.push(...(coords.length ? decoded.slice(1) : decoded))
      }
      return coords
    })
  }

  const features = geojson.geometries.map(geom => {
    let coordinates
    if (geom.type === 'Polygon') {
      coordinates = decodeRings(geom.arcs)
    } else if (geom.type === 'MultiPolygon') {
      coordinates = geom.arcs.map(polygon => decodeRings(polygon))
    } else {
      coordinates = []
    }
    return {
      type: 'Feature',
      properties: geom.properties || {},
      id: geom.id,
      geometry: { type: geom.type, coordinates },
    }
  })

  return { type: 'FeatureCollection', features }
}
