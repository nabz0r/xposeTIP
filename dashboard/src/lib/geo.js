/**
 * Shared geo utilities for WorkspaceGeoMap + LocationMap.
 *
 * - useWorldData(): fetches /world-110m.json once per session, returns { features, isoMap }
 * - projection / pathGenerator: d3.geoNaturalEarth1 fitted to viewBox
 * - COUNTRY_CENTROIDS: ISO alpha-2 → [lat, lng] for ground-truth pins
 * - useZoom(): D3 zoom behavior attached to an SVG ref, returns current { k, x, y }
 */
import { useEffect, useRef, useState } from 'react'
import { feature } from 'topojson-client'
import * as d3 from 'd3'

export const MAP_WIDTH = 960
export const MAP_HEIGHT = 480

// Module-level cache so multiple components share the same fetch
let _worldDataPromise = null

function loadWorldData() {
  if (_worldDataPromise) return _worldDataPromise
  _worldDataPromise = fetch('/world-110m.json')
    .then((r) => {
      if (!r.ok) throw new Error(`world-110m fetch failed: ${r.status}`)
      return r.json()
    })
    .then((topology) => {
      const collection = feature(topology, topology.objects.countries)
      const features = collection.features
      const isoMap = {}
      for (const f of features) {
        if (f.id) isoMap[String(f.id)] = f
        if (f.properties?.name) isoMap[`name:${f.properties.name}`] = f
      }
      return { features, isoMap }
    })
    .catch((err) => {
      _worldDataPromise = null
      throw err
    })
  return _worldDataPromise
}

export function useWorldData() {
  const [data, setData] = useState(null)
  const [error, setError] = useState(null)

  useEffect(() => {
    let cancelled = false
    loadWorldData()
      .then((d) => { if (!cancelled) setData(d) })
      .catch((e) => { if (!cancelled) setError(e) })
    return () => { cancelled = true }
  }, [])

  return { data, error, loading: !data && !error }
}

export function createProjection() {
  return d3.geoNaturalEarth1()
    .scale(MAP_WIDTH / (2 * Math.PI) * 1.15)
    .translate([MAP_WIDTH / 2, MAP_HEIGHT / 2 + 20])
}

export function createPathGenerator(projection) {
  return d3.geoPath(projection)
}

export function projectPoint(projection, lat, lng) {
  const out = projection([lng, lat])
  if (!out) return null
  return [out[0], out[1]]
}

export const ISO_ALPHA2_TO_NUMERIC = {
  US: '840', GB: '826', FR: '250', DE: '276', CA: '124', AU: '036', JP: '392',
  CN: '156', IN: '356', BR: '076', RU: '643', KR: '410', IT: '380', ES: '724',
  MX: '484', NL: '528', SE: '752', NO: '578', DK: '208', FI: '246', PL: '616',
  CH: '756', AT: '040', BE: '056', PT: '620', IE: '372', IL: '376', AE: '784',
  SA: '682', EG: '818', ZA: '710', NG: '566', KE: '404', TR: '792', UA: '804',
  AR: '032', CL: '152', CO: '170', PH: '608', TH: '764', MY: '458', SG: '702',
  ID: '360', VN: '704', PK: '586', LU: '442', HK: '344', TW: '158', NZ: '554',
  GR: '300', CZ: '203', RO: '642', HU: '348', BG: '100',
}

export const COUNTRY_CENTROIDS = {
  US: [39.8, -98.5], GB: [54.0, -2.0], FR: [46.6, 2.2], DE: [51.2, 10.4], CA: [56.1, -106.3],
  AU: [-25.3, 133.8], JP: [36.2, 138.3], CN: [35.9, 104.2], IN: [20.6, 79.0], BR: [-14.2, -51.9],
  RU: [61.5, 105.3], KR: [35.9, 127.8], IT: [41.9, 12.5], ES: [40.5, -3.7], MX: [23.6, -102.6],
  NL: [52.1, 5.3], SE: [60.1, 18.6], NO: [60.5, 8.5], DK: [56.3, 9.5], FI: [61.9, 25.7],
  PL: [51.9, 19.1], CH: [46.8, 8.2], AT: [47.5, 14.6], BE: [50.5, 4.5], PT: [39.4, -8.2],
  IE: [53.4, -8.2], IL: [31.0, 34.9], AE: [23.4, 53.8], SA: [23.9, 45.1], EG: [26.8, 30.8],
  ZA: [-30.6, 22.9], NG: [9.1, 8.7], KE: [-0.02, 37.9], TR: [39.0, 35.2], UA: [48.4, 31.2],
  AR: [-38.4, -63.6], CL: [-35.7, -71.5], CO: [4.6, -74.3], PH: [12.9, 121.8], TH: [15.9, 100.9],
  MY: [4.2, 101.9], SG: [1.4, 103.8], ID: [-0.8, 113.9], VN: [14.1, 108.3], PK: [30.4, 69.3],
  LU: [49.8, 6.1], HK: [22.4, 114.1], TW: [23.7, 121.0], NZ: [-40.9, 174.9], GR: [39.1, 21.8],
  CZ: [49.8, 15.5], RO: [45.9, 25.0], HU: [47.2, 19.5], BG: [42.7, 25.5],
}

/**
 * D3 zoom + pan behavior. Attach to an SVG ref + inner <g> ref. Constrains
 * scale 1..8, pan within viewBox bounds.
 */
export function useZoom(svgRef, gRef, { minScale = 1, maxScale = 8 } = {}) {
  const [transform, setTransform] = useState({ k: 1, x: 0, y: 0 })

  useEffect(() => {
    if (!svgRef.current || !gRef.current) return

    const svg = d3.select(svgRef.current)
    const g = d3.select(gRef.current)

    const zoom = d3.zoom()
      .scaleExtent([minScale, maxScale])
      .translateExtent([[0, 0], [MAP_WIDTH, MAP_HEIGHT]])
      .on('zoom', (event) => {
        g.attr('transform', event.transform)
        setTransform({ k: event.transform.k, x: event.transform.x, y: event.transform.y })
      })

    svg.call(zoom)

    return () => {
      svg.on('.zoom', null)
    }
  }, [svgRef, gRef, minScale, maxScale])

  return transform
}
