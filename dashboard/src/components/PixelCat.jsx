/**
 * PixelCat — 16×16 pixel art cat companion.
 *
 * Driven by fingerprint_avatar_seed (same seed as GenerativeAvatar).
 * 8 poses map to xposeTIP pipeline phases. Click for meow toast,
 * Konami for moonwalk, idle tail wag, hover-eye expression cycle.
 *
 * Default render = SVG with shape-rendering:crispEdges to preserve hard pixels.
 */

import React, { useState, useEffect, useRef, useMemo } from 'react'
import { deriveCatTraits, deriveBehavioralDetails } from '../lib/catSeed'

const KONAMI = ['ArrowUp','ArrowUp','ArrowDown','ArrowDown','ArrowLeft','ArrowRight','ArrowLeft','ArrowRight','b','a']

// Each pose = array of rects [col, row, w, h, kind] in 16-wide pixel grid.
// kind ∈ 'fur' | 'belly' | 'eye' | 'nose' | 'collar' | 'mouth'
// extras = JSX rendered AFTER the cat (smell trail, keyboard, book, Zzz...)
// All x/y in pixel-grid units; component scales to `size` prop.

const POSES = {
  idle: {
    rects: [
      // ears
      [2,0,2,1,'fur'], [12,0,2,1,'fur'],
      [1,1,4,1,'fur'], [11,1,4,1,'fur'],
      // head
      [3,2,10,1,'fur'],
      [2,3,12,2,'fur'],
      [2,5,3,1,'fur'], [5,5,1,1,'eye'], [6,5,4,1,'fur'], [10,5,1,1,'eye'], [11,5,3,1,'fur'],
      [2,6,12,1,'fur'],
      [2,7,5,1,'fur'], [7,7,2,1,'nose'], [9,7,5,1,'fur'],
      [3,8,10,1,'fur'],
      // body
      [4,9,2,1,'fur'], [6,9,4,1,'belly'], [10,9,2,1,'fur'],
      [4,10,1,1,'fur'], [5,10,6,1,'belly'], [11,10,1,1,'fur'],
      [4,11,1,1,'fur'], [5,11,6,1,'belly'], [11,11,1,1,'fur'],
      [4,12,8,1,'fur'],
      // collar
      [5,9,6,1,'collar'],
      // paws
      [3,13,2,1,'fur'], [11,13,2,1,'fur'],
      // tail (curled right)
      [12,9,1,1,'fur'], [13,8,1,1,'fur'], [13,7,1,1,'fur'],
    ],
  },

  sniff: {
    rects: [
      // ear (one visible, head turned)
      [10,1,2,1,'fur'], [9,2,4,1,'fur'],
      // long head reaching left-down
      [3,3,10,1,'fur'],
      [1,4,12,2,'fur'],
      [0,6,13,1,'fur'],
      [0,7,2,1,'nose'], [2,7,9,1,'fur'], [11,7,1,1,'eye'], [12,7,1,1,'fur'],
      [1,8,12,1,'fur'],
      // body
      [4,9,8,1,'fur'],
      [3,10,2,1,'fur'], [5,10,6,1,'belly'], [11,10,2,1,'fur'],
      [3,11,2,1,'fur'], [5,11,6,1,'belly'], [11,11,2,1,'fur'],
      [4,12,8,1,'fur'],
      // collar (slightly stretched)
      [5,9,6,1,'collar'],
      // paws
      [3,13,2,1,'fur'], [11,13,2,1,'fur'],
      // tail
      [12,9,1,1,'fur'], [13,8,1,1,'fur'],
    ],
    extras: ({px, fur}) => (
      <g>
        <circle cx={-1.5*px} cy={7.5*px} r={px*0.3} fill="#888"/>
        <circle cx={-3*px} cy={6.5*px} r={px*0.25} fill="#666"/>
        <circle cx={-4.5*px} cy={5.5*px} r={px*0.2} fill="#444"/>
      </g>
    ),
  },

  dig: {
    rects: [
      // ears
      [2,0,2,1,'fur'], [12,0,2,1,'fur'],
      [1,1,4,1,'fur'], [11,1,4,1,'fur'],
      // head
      [2,2,12,2,'fur'],
      [2,4,3,1,'fur'], [5,4,1,1,'eye'], [6,4,4,1,'fur'], [10,4,1,1,'eye'], [11,4,3,1,'fur'],
      [2,5,5,1,'fur'], [7,5,2,1,'nose'], [9,5,5,1,'fur'],
      [3,6,10,1,'fur'],
      // body (compressed, butt-up)
      [3,7,10,1,'fur'],
      [3,8,2,1,'fur'], [5,8,6,1,'belly'], [11,8,2,1,'fur'],
      [3,9,2,1,'fur'], [5,9,6,1,'belly'], [11,9,2,1,'fur'],
      [4,7,8,1,'collar'],
      // raised front paws (digging)
      [0,7,2,1,'fur'], [14,7,2,1,'fur'],
      [-1,8,2,1,'fur'], [15,8,2,1,'fur'],
      // back legs
      [4,10,8,1,'fur'],
      [3,11,2,1,'fur'], [11,11,2,1,'fur'],
      // tail up
      [13,5,1,1,'fur'], [13,4,1,1,'fur'], [13,3,1,1,'fur'],
    ],
    extras: ({px}) => (
      <g>
        <circle cx={-2*px} cy={4*px} r={px*0.35} fill="#7a5230"/>
        <circle cx={-3*px} cy={2*px} r={px*0.3} fill="#7a5230"/>
        <circle cx={17*px} cy={4*px} r={px*0.35} fill="#7a5230"/>
        <circle cx={18*px} cy={2*px} r={px*0.3} fill="#7a5230"/>
      </g>
    ),
  },

  type: {
    rects: [
      // ears
      [2,0,2,1,'fur'], [12,0,2,1,'fur'],
      [1,1,4,1,'fur'], [11,1,4,1,'fur'],
      // head
      [2,2,12,2,'fur'],
      [2,4,3,1,'fur'], [5,4,1,1,'eye'], [6,4,4,1,'fur'], [10,4,1,1,'eye'], [11,4,3,1,'fur'],
      [2,5,5,1,'fur'], [7,5,2,1,'nose'], [9,5,5,1,'fur'],
      [3,6,10,1,'fur'],
      // body
      [3,7,10,1,'fur'],
      [2,8,12,1,'fur'],
      [3,8,10,1,'belly'],
      [3,9,10,1,'fur'],
      // collar
      [4,7,8,1,'collar'],
      // forward paws extended
      [1,10,2,1,'fur'], [13,10,2,1,'fur'],
      // keyboard pixel row
    ],
    extras: ({px}) => (
      <g>
        <rect x={-2*px} y={11*px} width={20*px} height={1.5*px} fill="#3388ff"/>
        <rect x={-2*px} y={11*px} width={20*px} height={0.25*px} fill="#00ff88"/>
        {Array.from({length:10}).map((_,i)=>(
          <rect key={i} x={(-1.5+i*2)*px} y={11.3*px} width={px*0.7} height={px*0.5} fill="#0a0a0f"/>
        ))}
      </g>
    ),
  },

  read: {
    rects: [
      // ears
      [2,0,2,1,'fur'], [12,0,2,1,'fur'],
      [1,1,4,1,'fur'], [11,1,4,1,'fur'],
      // head tilted down toward book
      [2,2,12,2,'fur'],
      [2,4,3,1,'fur'], [5,4,1,1,'eye'], [6,4,4,1,'fur'], [10,4,1,1,'eye'], [11,4,3,1,'fur'],
      [2,5,5,1,'fur'], [7,5,2,1,'nose'], [9,5,5,1,'fur'],
      [3,6,10,1,'fur'],
      // body
      [3,7,10,1,'fur'],
      [3,8,10,1,'belly'],
      [3,9,10,1,'fur'],
      [4,7,8,1,'collar'],
      // paws
      [3,10,2,1,'fur'], [11,10,2,1,'fur'],
    ],
    extras: ({px}) => (
      <g>
        {/* open book in front of cat */}
        <rect x={-2.5*px} y={7*px} width={5.5*px} height={3.5*px} fill="#eeeeee"/>
        <rect x={-2.5*px} y={7*px} width={5.5*px} height={px*0.5} fill="#888"/>
        <line x1={-2*px} y1={8*px} x2={2.5*px} y2={8*px} stroke="#444" strokeWidth={px*0.25}/>
        <line x1={-2*px} y1={9*px} x2={1.5*px} y2={9*px} stroke="#444" strokeWidth={px*0.25}/>
        <line x1={-2*px} y1={10*px} x2={2*px} y2={10*px} stroke="#444" strokeWidth={px*0.25}/>
      </g>
    ),
  },

  compute: {
    rects: [
      // ears
      [2,0,2,1,'fur'], [12,0,2,1,'fur'],
      [1,1,4,1,'fur'], [11,1,4,1,'fur'],
      // head (looking up at easel)
      [2,2,12,2,'fur'],
      [2,4,3,1,'fur'], [5,4,1,1,'eye'], [6,4,4,1,'fur'], [10,4,1,1,'eye'], [11,4,3,1,'fur'],
      [2,5,5,1,'fur'], [7,5,2,1,'nose'], [9,5,5,1,'fur'],
      [3,6,10,1,'fur'],
      // body (sitting)
      [4,7,8,1,'fur'],
      [3,8,2,1,'fur'], [5,8,6,1,'belly'], [11,8,2,1,'fur'],
      [3,9,2,1,'fur'], [5,9,6,1,'belly'], [11,9,2,1,'fur'],
      [4,10,8,1,'fur'],
      [5,7,6,1,'collar'],
      // raised paw with brush
      [-1,5,2,1,'fur'],
      [3,11,2,1,'fur'], [11,11,2,1,'fur'],
    ],
    extras: ({px}) => (
      <g>
        {/* easel/canvas to the left */}
        <rect x={-6*px} y={1*px} width={4*px} height={8*px} fill="#3a3a3a"/>
        <rect x={-5.5*px} y={1.5*px} width={3*px} height={5*px} fill="#eeeeee"/>
        {/* swirl marks on canvas */}
        <circle cx={-4*px} cy={3*px} r={px*0.6} fill="none" stroke="#00ff88" strokeWidth={px*0.3}/>
        <line x1={-4.5*px} y1={5*px} x2={-3*px} y2={5*px} stroke="#3388ff" strokeWidth={px*0.3}/>
        {/* brush tip */}
        <rect x={-2*px} y={4.5*px} width={px*0.6} height={px*0.6} fill="#00ff88"/>
      </g>
    ),
  },

  compare: {
    rects: [
      // ears
      [2,0,2,1,'fur'], [12,0,2,1,'fur'],
      [1,1,4,1,'fur'], [11,1,4,1,'fur'],
      // head
      [2,2,12,2,'fur'],
      [2,4,3,1,'fur'], [5,4,1,1,'eye'], [6,4,4,1,'fur'], [10,4,1,1,'eye'], [11,4,3,1,'fur'],
      [2,5,5,1,'fur'], [7,5,2,1,'nose'], [9,5,5,1,'fur'],
      [3,6,10,1,'fur'],
      // body sitting
      [4,7,8,1,'fur'],
      [3,8,2,1,'fur'], [5,8,6,1,'belly'], [11,8,2,1,'fur'],
      [3,9,2,1,'fur'], [5,9,6,1,'belly'], [11,9,2,1,'fur'],
      [4,10,8,1,'fur'],
      [5,7,6,1,'collar'],
      [3,11,2,1,'fur'], [11,11,2,1,'fur'],
    ],
    extras: ({px}) => (
      <g>
        {/* two photos held up, one on each side */}
        <rect x={-3*px} y={3*px} width={3*px} height={4*px} fill="#eeeeee"/>
        <rect x={-2.5*px} y={3.5*px} width={2*px} height={2*px} fill="#3388ff" opacity="0.6"/>
        <rect x={16*px} y={3*px} width={3*px} height={4*px} fill="#eeeeee"/>
        <rect x={16.5*px} y={3.5*px} width={2*px} height={2*px} fill="#3388ff" opacity="0.6"/>
        {/* equals sign between */}
        <rect x={6.5*px} y={-2*px} width={3*px} height={px*0.4} fill="#00ff88"/>
        <rect x={6.5*px} y={-0.5*px} width={3*px} height={px*0.4} fill="#00ff88"/>
      </g>
    ),
  },

  sleep: {
    rects: [
      // ears (folded)
      [5,0,2,1,'fur'], [9,0,2,1,'fur'],
      [4,1,3,1,'fur'], [9,1,3,1,'fur'],
      // curled body (oval)
      [3,2,9,2,'fur'],
      [2,4,11,1,'fur'],
      [1,5,13,2,'fur'],
      [1,7,13,2,'fur'],
      [2,9,11,1,'fur'],
      [3,10,9,1,'fur'],
      // closed eyes (lines)
      [4,5,2,1,'eye'], [10,5,2,1,'eye'],
      // nose tucked
      [7,6,1,1,'nose'],
      // belly visible (curled)
      [3,7,9,1,'belly'],
    ],
    extras: ({px}) => (
      <g>
        <text x={13*px} y={-1*px} fontFamily="monospace" fontSize={px*1.5} fill="#666">z</text>
        <text x={15*px} y={-3*px} fontFamily="monospace" fontSize={px*1.8} fill="#888">z</text>
        <text x={17*px} y={-6*px} fontFamily="monospace" fontSize={px*2.2} fill="#aaa">Z</text>
      </g>
    ),
  },
}

/**
 * Deduce the pose from a scan + scraperProgress payload.
 * Pure function, exported for direct use by callers that don't have
 * the full <PixelCat /> render pipeline (e.g. tabs).
 */
export function phaseFromScan(scan, scraperProgress) {
  if (!scan) return 'idle'
  const mp = scan.module_progress || {}

  if (scan.status === 'queued') return 'idle'
  if (Object.values(mp).every(v => v === 'queued')) return 'idle'

  if (scan.status === 'completed') {
    if (scan.cascade_state === 'gathering') return 'read'
    if (scan.cascade_state === 'computing') return 'compute'
    if (scan.cascade_state === 'similarity') return 'compare'
    return 'sleep'
  }

  // status === 'running'
  if (mp.scraper_engine === 'running') return 'type'
  if (Object.values(mp).some(v => v === 'running')) return 'sniff'
  return 'idle'
}

// ─────────────────────────────────────────────────────────────
// S221 detail-layer overlays
// Rendered AFTER the base pose rects, BEFORE pose extras.
// Pose-agnostic only — pose-aware overlays (tuxedo, mitten) deferred.
// ─────────────────────────────────────────────────────────────

function PatternOverlay({ pattern, px, fur, belly }) {
  if (pattern === 'solid') return null
  if (pattern === 'tabby') {
    const stripe = darken(fur, 30)
    return (
      <g>
        <rect x={4 * px} y={9.3 * px} width={8 * px} height={px * 0.4} fill={stripe}/>
        <rect x={4 * px} y={10.3 * px} width={8 * px} height={px * 0.4} fill={stripe}/>
        <rect x={4 * px} y={11.3 * px} width={8 * px} height={px * 0.4} fill={stripe}/>
      </g>
    )
  }
  if (pattern === 'spots') {
    const spot = darken(fur, 35)
    return (
      <g>
        <rect x={4 * px} y={9 * px} width={px} height={px} fill={spot}/>
        <rect x={9 * px} y={9 * px} width={px} height={px} fill={spot}/>
        <rect x={6 * px} y={10 * px} width={px} height={px} fill={spot}/>
        <rect x={11 * px} y={10 * px} width={px} height={px} fill={spot}/>
        <rect x={5 * px} y={11 * px} width={px} height={px} fill={spot}/>
        <rect x={10 * px} y={11 * px} width={px} height={px} fill={spot}/>
      </g>
    )
  }
  if (pattern === 'bicolor') {
    return <rect x={8 * px} y={3 * px} width={6 * px} height={10 * px} fill="#f0f0e8" opacity="0.6"/>
  }
  if (pattern === 'calico') {
    return (
      <g>
        <rect x={3 * px} y={3 * px} width={4 * px} height={3 * px} fill="#f0e6c8" opacity="0.55"/>
        <rect x={9 * px} y={9 * px} width={3 * px} height={3 * px} fill="#d4a070" opacity="0.55"/>
      </g>
    )
  }
  if (pattern === 'ticked') {
    const tick = darken(fur, 20)
    return (
      <g>
        {[3, 5, 7, 9, 11].flatMap((c) => [9, 10, 11].map((r) => (
          <rect key={`${c}-${r}`} x={c * px + px * 0.3} y={r * px + px * 0.3} width={px * 0.4} height={px * 0.4} fill={tick}/>
        )))}
      </g>
    )
  }
  return null
}

function MarkingOverlay({ marking, px, fur, eye }) {
  if (marking === 'none') return null
  if (marking === 'mask') {
    return <rect x={2 * px} y={4.6 * px} width={12 * px} height={px * 0.8} fill="#0a0a0f" opacity="0.55"/>
  }
  if (marking === 'blaze') {
    return <rect x={7 * px} y={2 * px} width={2 * px} height={5 * px} fill="#f0f0e8" opacity="0.7"/>
  }
  if (marking === 'whiskers') {
    return (
      <g stroke="#f0f0e8" strokeWidth={px * 0.2} opacity="0.7">
        <line x1={2 * px} y1={7 * px} x2={5 * px} y2={7 * px}/>
        <line x1={2 * px} y1={7.5 * px} x2={5 * px} y2={7.5 * px}/>
        <line x1={11 * px} y1={7 * px} x2={14 * px} y2={7 * px}/>
        <line x1={11 * px} y1={7.5 * px} x2={14 * px} y2={7.5 * px}/>
      </g>
    )
  }
  if (marking === 'nose_spot') {
    return <rect x={6 * px} y={6 * px} width={4 * px} height={2 * px} fill="#f0e6c8" opacity="0.5"/>
  }
  return null
}

function AccessoryOverlay({ accessory, px, collar }) {
  if (accessory === 'none') return null
  if (accessory === 'glasses') {
    return (
      <g fill="none" stroke="#0a0a0f" strokeWidth={px * 0.35}>
        <rect x={4 * px} y={4.5 * px} width={3 * px} height={2 * px}/>
        <rect x={9 * px} y={4.5 * px} width={3 * px} height={2 * px}/>
        <line x1={7 * px} y1={5.5 * px} x2={9 * px} y2={5.5 * px}/>
      </g>
    )
  }
  if (accessory === 'bowtie') {
    return (
      <g fill={collar}>
        <polygon points={`${6 * px},${9 * px} ${8 * px},${9.5 * px} ${6 * px},${10 * px}`}/>
        <polygon points={`${10 * px},${9 * px} ${8 * px},${9.5 * px} ${10 * px},${10 * px}`}/>
        <rect x={7.6 * px} y={9.3 * px} width={px * 0.8} height={px * 0.5} fill="#0a0a0f"/>
      </g>
    )
  }
  if (accessory === 'scarf') {
    return <rect x={3 * px} y={8.5 * px} width={10 * px} height={1.5 * px} fill={collar}/>
  }
  if (accessory === 'badge') {
    return (
      <g>
        <circle cx={11 * px} cy={10 * px} r={px * 0.6} fill="#ffcc00"/>
        <text x={11 * px} y={10.3 * px} fontSize={px * 0.8} fill="#0a0a0f" textAnchor="middle">!</text>
      </g>
    )
  }
  return null
}

// Tiny color helper — darken a hex by N%
function darken(hex, pct) {
  const h = hex.replace('#', '')
  const r = parseInt(h.slice(0, 2), 16)
  const g = parseInt(h.slice(2, 4), 16)
  const b = parseInt(h.slice(4, 6), 16)
  const f = (n) => Math.max(0, Math.min(255, Math.floor(n * (100 - pct) / 100)))
  return `#${f(r).toString(16).padStart(2, '0')}${f(g).toString(16).padStart(2, '0')}${f(b).toString(16).padStart(2, '0')}`
}

export default function PixelCat({
  seed,
  pose = 'idle',
  size = 64,
  animated = true,
  onClick,
  behavioralHash = null,
}) {
  const traits = useMemo(() => deriveCatTraits(seed), [seed])
  const details = useMemo(() => deriveBehavioralDetails(behavioralHash), [behavioralHash])
  const [tailFrame, setTailFrame] = useState(0)
  // S221: baseline expression is behavioral-derived; hover still cycles on top
  const expressionBaseline = { chill: 0, alert: 1, curious: 2, sleepy: 3 }[details.expression] ?? 0
  const [expressionDelta, setExpressionDelta] = useState(0)
  const expression = (expressionBaseline + expressionDelta) % 4
  const [moonwalk, setMoonwalk] = useState(false)
  const [meow, setMeow] = useState(false)
  const konamiBuf = useRef([])

  // Tail wag — random idle pulse every 6–10s, except when sleeping
  useEffect(() => {
    if (!animated || pose === 'sleep') return
    let id
    const schedule = () => {
      id = setTimeout(() => {
        setTailFrame(f => (f + 1) % 4)
        schedule()
      }, 6000 + Math.random() * 4000)
    }
    schedule()
    return () => clearTimeout(id)
  }, [animated, pose])

  // Konami listener — fires moonwalk for 2.5s
  useEffect(() => {
    if (!animated) return
    const onKey = (e) => {
      konamiBuf.current.push(e.key)
      if (konamiBuf.current.length > KONAMI.length) konamiBuf.current.shift()
      if (konamiBuf.current.length === KONAMI.length &&
          konamiBuf.current.every((k, i) => k.toLowerCase() === KONAMI[i].toLowerCase())) {
        setMoonwalk(true)
        setTimeout(() => setMoonwalk(false), 2500)
        konamiBuf.current = []
      }
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [animated])

  const handleClick = (e) => {
    setMeow(true)
    setTimeout(() => setMeow(false), 1200)
    if (onClick) onClick(e)
  }

  const poseSpec = POSES[pose] || POSES.idle
  const px = size / 16
  const colorFor = (kind) => {
    if (kind === 'eye') {
      // 4 expressions: chill(0)=open, alert(1)=wider, curious(2)=narrow, sleepy(3)=closed-line
      if (expression === 3) return traits.fur  // sleepy → eye blends into fur
      return traits.eye
    }
    if (kind === 'belly') return traits.belly
    if (kind === 'nose') return traits.nose
    if (kind === 'collar') return traits.collar
    if (kind === 'mouth') return traits.nose
    return traits.fur
  }

  // SVG width must accommodate extras that overflow the 16x16 grid (sniff trail,
  // dig dirt, keyboard, easel, photos, Zzz). Reserve 8 extra px each side and top.
  const padX = 8
  const padTop = 10
  const svgW = size + padX * 2
  const svgH = size + padTop + 4

  return (
    <div style={{ position: 'relative', display: 'inline-block' }}>
      <svg
        width={svgW}
        height={svgH}
        viewBox={`${-padX} ${-padTop} ${svgW} ${svgH}`}
        shapeRendering="crispEdges"
        onClick={handleClick}
        style={{
          cursor: 'pointer',
          transform: moonwalk ? 'translateX(-12px) rotate(-8deg)' : 'none',
          transition: 'transform 0.3s ease-in-out',
        }}
      >
        {/* Tail wag offset: shift last rect group by tailFrame */}
        <g style={{ transform: `translateX(${tailFrame % 2 === 0 ? 0 : 0.3}px)` }}>
          {poseSpec.rects.map((r, i) => {
            const [c, row, w, h, kind] = r
            // Eye rects get hover handlers
            if (kind === 'eye') {
              return (
                <rect
                  key={i}
                  x={c * px}
                  y={row * px}
                  width={w * px}
                  height={h * px}
                  fill={colorFor(kind)}
                  onMouseEnter={() => setExpressionDelta((d) => (d + 1) % 4)}
                />
              )
            }
            return (
              <rect
                key={i}
                x={c * px}
                y={row * px}
                width={w * px}
                height={h * px}
                fill={colorFor(kind)}
              />
            )
          })}
        </g>
        <PatternOverlay pattern={details.pattern} px={px} fur={traits.fur} belly={traits.belly}/>
        <MarkingOverlay marking={details.marking} px={px} fur={traits.fur} eye={traits.eye}/>
        <AccessoryOverlay accessory={details.accessory} px={px} collar={traits.collar}/>
        {poseSpec.extras && poseSpec.extras({ px, fur: traits.fur })}
      </svg>
      {meow && (
        <div style={{
          position: 'absolute',
          top: -size * 0.4,
          left: size * 0.6,
          background: '#0a0a0f',
          border: '1px solid #00ff88',
          color: '#00ff88',
          fontFamily: 'monospace',
          fontSize: Math.max(10, size * 0.18),
          padding: '2px 6px',
          borderRadius: 4,
          pointerEvents: 'none',
          animation: 'fadeOut 1.2s ease-out forwards',
        }}>
          meow
        </div>
      )}
      <style>{`
        @keyframes fadeOut {
          0%   { opacity: 1; transform: translateY(0); }
          80%  { opacity: 1; transform: translateY(-4px); }
          100% { opacity: 0; transform: translateY(-8px); }
        }
      `}</style>
    </div>
  )
}
