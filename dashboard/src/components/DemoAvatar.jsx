import { useEffect, useMemo, useRef, useState } from 'react'
import PixelCat from './PixelCat'

// S250 — Matrix-scramble avatar wrapper. Renders PixelCat (untouched) below,
// then an SVG overlay of 16×16 cells that scramble (green family flicker)
// while phase='scramble', resolve zone-by-zone over `resolveMs` while
// phase='resolving' (eyes → head → torso → base), and disappear entirely
// when phase='resolved'. PixelCat geometry mirrored exactly:
//   padX=8, padTop=10, svgW=size+16, svgH=size+14, content origin (0,0),
//   px = size/16, content fills rows 0–15 × cols 0–15.

const PAD_X = 8
const PAD_TOP = 10
const ROWS = 16
const COLS = 16

const SCRAMBLE_PALETTE = ['#00ff88', '#00cc6a', '#0f6', '#063', '#0fa', '#1a7f4f']
const TICK_MS = 100 // scramble re-randomize cadence

// Eye footprint per measured PixelCat poses (rows 4-5, cols 4-11)
function zoneOf(row, col) {
  const isEye = row >= 4 && row <= 5 && col >= 4 && col <= 11
  if (isEye) return 'eyes'
  if (row <= 8) return 'head'
  if (row <= 11) return 'torso'
  return 'base'
}

const ZONE_WINDOW = {
  eyes:  [0.00, 0.25],
  head:  [0.25, 0.50],
  torso: [0.50, 0.75],
  base:  [0.75, 1.00],
}

// Deterministic pseudo-random per (row,col) for jitter inside a zone.
function hashFloat(row, col, salt = 0) {
  let x = row * 31 + col * 7 + salt * 1009
  x = (x ^ (x << 13)) >>> 0
  x = (x ^ (x >> 17)) >>> 0
  x = (x ^ (x << 5)) >>> 0
  return (x % 10000) / 10000
}

// Pre-bake one threshold per cell with deterministic jitter inside its zone.
function buildThresholds() {
  const out = []
  for (let row = 0; row < ROWS; row++) {
    for (let col = 0; col < COLS; col++) {
      const z = zoneOf(row, col)
      const [lo, hi] = ZONE_WINDOW[z]
      // Spread cells uniformly across the zone window using a stable hash.
      const t = lo + (hi - lo) * hashFloat(row, col)
      out.push({ row, col, zone: z, threshold: t })
    }
  }
  return out
}

export default function DemoAvatar({
  seed,
  behavioralHash,
  pose = 'idle',
  size = 140,
  phase = 'scramble',
  resolveMs = 7000,
}) {
  const cells = useMemo(buildThresholds, [])
  const [progress, setProgress] = useState(phase === 'resolved' ? 1 : 0)
  const [, setTick] = useState(0) // forces re-render for scramble flicker
  const rafRef = useRef(null)
  const tickRef = useRef(null)

  // Drive `progress` based on phase.
  useEffect(() => {
    cancelAnimationFrame(rafRef.current)
    if (phase === 'scramble') {
      setProgress(0)
      return
    }
    if (phase === 'resolved') {
      setProgress(1)
      return
    }
    // phase === 'resolving' → animate 0 → 1 over resolveMs
    const start = performance.now()
    const tick = (now) => {
      const t = Math.min(1, (now - start) / Math.max(1, resolveMs))
      setProgress(t)
      if (t < 1) rafRef.current = requestAnimationFrame(tick)
    }
    rafRef.current = requestAnimationFrame(tick)
    return () => cancelAnimationFrame(rafRef.current)
  }, [phase, resolveMs])

  // Scramble flicker — re-render on a fixed cadence while anything is unrevealed.
  useEffect(() => {
    if (phase === 'resolved') return
    tickRef.current = setInterval(() => {
      setTick((t) => (t + 1) % 1_000_000)
    }, TICK_MS)
    return () => clearInterval(tickRef.current)
  }, [phase])

  const px = size / 16
  const svgW = size + PAD_X * 2
  const svgH = size + PAD_TOP + 4

  // PixelCat receives behavioralHash only once we leave 'scramble' — so
  // the behavioral detail layer "appears" as the resolution begins.
  const passedHash = phase === 'scramble' ? null : behavioralHash

  // If fully resolved, skip overlay entirely (cleanest DOM).
  if (phase === 'resolved') {
    return (
      <PixelCat
        seed={seed}
        behavioralHash={behavioralHash}
        pose={pose}
        size={size}
        animated
      />
    )
  }

  return (
    <div className="relative inline-block" style={{ width: svgW, height: svgH }}>
      <PixelCat
        seed={seed}
        behavioralHash={passedHash}
        pose={pose}
        size={size}
        animated
      />
      <svg
        className="absolute inset-0 pointer-events-none"
        width={svgW}
        height={svgH}
        viewBox={`${-PAD_X} ${-PAD_TOP} ${svgW} ${svgH}`}
        xmlns="http://www.w3.org/2000/svg"
      >
        {cells.map((c) => {
          if (c.threshold <= progress) return null // resolved → reveal underneath
          // Color jitter — recomputed each tick (state setTick forces re-render).
          const colorIdx = Math.floor(Math.random() * SCRAMBLE_PALETTE.length)
          const fill = SCRAMBLE_PALETTE[colorIdx]
          // Opacity flickers between 0.55 and 1.0; cells closer to their reveal
          // threshold fade out slightly so the wave feels organic.
          const reveal_gap = c.threshold - progress
          const fadeOut = Math.max(0, 1 - reveal_gap * 8)
          const baseAlpha = 0.55 + Math.random() * 0.45
          const opacity = baseAlpha * (1 - fadeOut * 0.6)
          return (
            <rect
              key={`${c.row}-${c.col}`}
              x={c.col * px}
              y={c.row * px}
              width={px}
              height={px}
              fill={fill}
              opacity={opacity}
              shapeRendering="crispEdges"
            />
          )
        })}
      </svg>
    </div>
  )
}
