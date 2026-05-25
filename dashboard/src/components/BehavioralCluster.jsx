/**
 * BehavioralCluster — soft UI nudge surfacing the K=3 clustering of
 * bfp_behavioral_hash_v1. Renders a compact row under ProfileHeader when
 * the target has 1+ behavioral twins in the same workspace.
 *
 * Hidden entirely when count === 0 (no hash, or single occupant of bucket).
 *
 * Tone: BFP-confident, matter-of-fact. The cluster is a positive signal —
 * the protocol successfully identified behavioral similarity, not a bug.
 */

import React, { useEffect, useState } from 'react'
import { ChevronDown, ChevronUp } from 'lucide-react'
import { Link } from 'react-router-dom'
import { getBehavioralTwins } from '../lib/api'
import PixelCat from './PixelCat'

export default function BehavioralCluster({ targetId, targetSeed, targetBehavioralHash }) {
  const [data, setData] = useState(null)
  const [open, setOpen] = useState(false)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!targetId) return
    let cancelled = false
    setLoading(true)
    getBehavioralTwins(targetId)
      .then((res) => { if (!cancelled) setData(res) })
      .catch(() => { if (!cancelled) setData({ count: 0, peers: [] }) })
      .finally(() => { if (!cancelled) setLoading(false) })
    return () => { cancelled = true }
  }, [targetId])

  // Hide entirely when no twins (and not still loading the first time)
  if (loading) return null
  if (!data || data.count === 0) return null

  return (
    <div className="bg-[#12121a] border border-[#1e1e2e] rounded-xl overflow-hidden">
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        className="w-full flex items-center justify-between px-4 py-2.5 hover:bg-[#1a1a26] transition-colors"
      >
        <div className="flex items-center gap-3">
          <PixelCat
            seed={targetSeed}
            behavioralHash={targetBehavioralHash}
            pose="idle"
            size={20}
            animated={false}
          />
          <span className="text-xs font-medium text-gray-300">
            Behavioral cluster
          </span>
          <span className="text-xs font-mono text-[#00ff88]">
            {data.count} {data.count === 1 ? 'peer' : 'peers'}
          </span>
          {data.prefix && (
            <span className="text-[10px] font-mono text-gray-500 hidden sm:inline">
              hash[:16] · {data.prefix.slice(0, 8)}…
            </span>
          )}
        </div>
        <div className="flex items-center gap-2 text-gray-500">
          <span className="text-[10px] hidden md:inline">
            same PixelCat detail layer
          </span>
          {open ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
        </div>
      </button>

      {open && (
        <div className="px-4 pb-3 border-t border-[#1e1e2e]">
          <div className="text-[11px] text-gray-500 mt-2 mb-2 leading-relaxed">
            These targets share this target's behavioral fingerprint cluster (BFP K=3, hash prefix match).
            By design — the visual match surfaces the protocol's clustering signal.
          </div>
          <div className="space-y-1">
            {data.peers.map((p) => (
              <Link
                key={p.target_id}
                to={`/targets/${p.target_id}`}
                className="flex items-center justify-between px-2 py-1.5 rounded hover:bg-[#1a1a26] transition-colors group"
              >
                <span className="text-xs font-mono text-gray-300 group-hover:text-white truncate">
                  {p.email}
                </span>
                {p.display_name && (
                  <span className="text-[10px] text-gray-500 truncate ml-2">
                    {p.display_name}
                  </span>
                )}
              </Link>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
