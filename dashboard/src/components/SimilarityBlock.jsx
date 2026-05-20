import React, { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Radar, ChevronRight, Clock } from 'lucide-react'
import { getSimilarTargets } from '../lib/api'

const scoreColor = (score) => {
  if (score == null) return '#666688'
  if (score >= 61) return '#ff2244'
  if (score >= 31) return '#ff8800'
  return '#00ff88'
}

const simColor = (sim) => {
  if (sim >= 0.95) return '#ff2244'
  if (sim >= 0.85) return '#ff8800'
  if (sim >= 0.75) return '#ffcc00'
  return '#3388ff'
}

const topAxisDiff = (diffs) => {
  if (!diffs) return null
  const entries = Object.entries(diffs)
  if (!entries.length) return null
  // Pick the axis with the largest absolute delta — what most distinguishes the pair
  const sorted = entries.sort((a, b) => Math.abs(b[1]) - Math.abs(a[1]))
  const [axis, delta] = sorted[0]
  if (Math.abs(delta) < 0.05) return null
  const sign = delta > 0 ? '+' : ''
  return `${axis}: ${sign}${delta.toFixed(2)}`
}

const relativeAge = (iso) => {
  if (!iso) return null
  const then = new Date(iso).getTime()
  if (Number.isNaN(then)) return null
  const days = Math.floor((Date.now() - then) / (1000 * 60 * 60 * 24))
  if (days < 1) return 'today'
  if (days === 1) return '1d ago'
  if (days < 7) return `${days}d ago`
  if (days < 30) return `${Math.floor(days / 7)}w ago`
  if (days < 365) return `${Math.floor(days / 30)}mo ago`
  return `${Math.floor(days / 365)}y ago`
}

export default function SimilarityBlock({ targetId }) {
  const [items, setItems] = useState(null)
  const [loading, setLoading] = useState(true)
  const navigate = useNavigate()

  useEffect(() => {
    if (!targetId) return
    let cancelled = false
    setLoading(true)
    getSimilarTargets(targetId, { limit: 5, minSimilarity: 0.7 })
      .then((res) => {
        if (cancelled) return
        setItems(res?.items || [])
      })
      .catch(() => {
        if (cancelled) return
        setItems([])
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })
    return () => {
      cancelled = true
    }
  }, [targetId])

  // Self-hide while loading the first time, when no neighbours, or on error
  if (loading || !items || items.length === 0) return null

  return (
    <div className="bg-[#12121a] border border-[#1e1e2e] rounded-xl p-5">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Radar className="w-4 h-4 text-[#aa66ff]" />
          <h3 className="text-xs font-semibold uppercase tracking-wider text-gray-400">
            Similar Identities <span className="text-gray-600">in this workspace</span>
          </h3>
        </div>
        <span
          className="text-xs font-mono font-bold px-2 py-0.5 rounded-full"
          style={{ backgroundColor: '#aa66ff26', color: '#aa66ff' }}
        >
          {items.length}
        </span>
      </div>

      <div className="space-y-2">
        {items.map((it) => {
          const sim = it.similarity
          const sc = simColor(sim)
          const escore = it.exposure_score
          const topDiff = topAxisDiff(it.axis_diffs)
          const detected = relativeAge(it.first_detected)
          return (
            <button
              key={it.target_id}
              onClick={() => navigate(`/targets/${it.target_id}`)}
              className="w-full bg-[#0a0a0f] border border-[#1e1e2e] hover:border-[#aa66ff]/40 rounded-lg p-3 flex items-center gap-3 transition-colors text-left"
            >
              <div className="shrink-0">
                {it.avatar_url ? (
                  <img
                    src={it.avatar_url}
                    alt=""
                    className="w-9 h-9 rounded-full object-cover"
                    onError={(e) => { e.target.style.display = 'none' }}
                  />
                ) : (
                  <div className="w-9 h-9 rounded-full bg-[#1e1e2e]" />
                )}
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <span className="text-sm font-medium truncate">
                    {it.display_name || it.email}
                  </span>
                  {it.display_name && (
                    <span className="text-[10px] text-gray-600 font-mono truncate">{it.email}</span>
                  )}
                </div>
                <div className="flex items-center gap-3 mt-0.5">
                  {topDiff && (
                    <span className="text-[10px] text-gray-500 font-mono">
                      Δ {topDiff}
                    </span>
                  )}
                  {detected && (
                    <span className="text-[10px] text-gray-600 flex items-center gap-0.5">
                      <Clock className="w-2.5 h-2.5" />
                      first matched {detected}
                    </span>
                  )}
                </div>
              </div>
              <div className="flex items-center gap-3 shrink-0">
                {escore != null && (
                  <div className="text-right">
                    <div className="text-[9px] text-gray-600 uppercase tracking-wider">Score</div>
                    <div className="text-sm font-bold font-mono" style={{ color: scoreColor(escore) }}>
                      {escore}
                    </div>
                  </div>
                )}
                <div className="text-right">
                  <div className="text-[9px] text-gray-600 uppercase tracking-wider">Match</div>
                  <div className="text-sm font-bold font-mono" style={{ color: sc }}>
                    {Math.round(sim * 100)}%
                  </div>
                </div>
                <ChevronRight className="w-4 h-4 text-gray-600" />
              </div>
            </button>
          )
        })}
      </div>
    </div>
  )
}
