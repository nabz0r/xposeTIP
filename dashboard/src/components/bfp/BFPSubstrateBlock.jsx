import React, { useEffect, useState } from 'react'
import { Fingerprint, ShieldCheck, Network } from 'lucide-react'
import { request } from '../../lib/api'

export default function BFPSubstrateBlock({ targetId }) {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [copied, setCopied] = useState(false)

  useEffect(() => {
    if (!targetId) return
    let cancelled = false
    setLoading(true)
    request(`/api/v1/targets/${targetId}/bfp`)
      .then(d => { if (!cancelled) { setData(d); setError(null) } })
      .catch(e => { if (!cancelled) setError(e) })
      .finally(() => { if (!cancelled) setLoading(false) })
    return () => { cancelled = true }
  }, [targetId])

  if (loading) return null  // silent skeleton
  if (error) return null    // silent fail — no error banner on Overview
  if (!data || !data.behavioral_hash?.present) return null  // no substrate yet

  const hashShort = data.behavioral_hash.short
  const hashFull = data.behavioral_hash.full
  const claimsTotal = data.claims.total
  const claimsByType = data.claims.by_type || {}
  const cvRatio = data.cross_verification.ratio
  const cvVerified = data.cross_verification.verified
  const cvTotal = data.cross_verification.total

  const copyHash = async () => {
    try {
      await navigator.clipboard.writeText(hashFull)
      setCopied(true)
      setTimeout(() => setCopied(false), 1500)
    } catch (e) {
      // silent — clipboard API not available
    }
  }

  const claimTypesSummary = Object.entries(claimsByType)
    .sort((a, b) => b[1] - a[1])
    .map(([t, c]) => `${t}:${c}`)
    .join(' · ')

  return (
    <div className="bg-[#12121a] border border-[#1e1e2e] rounded-xl p-5">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-xs font-semibold uppercase tracking-wider text-gray-500">
          BFP Substrate
        </h3>
        <span className="text-[10px] text-gray-600 font-mono">v1 · trust layer</span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
        {/* Behavioral hash */}
        <div className="bg-[#0a0a0f] border border-[#1e1e2e] rounded-lg p-4">
          <div className="flex items-center gap-2 mb-3">
            <Fingerprint className="w-4 h-4 text-[#aa66ff]" />
            <span className="text-xs font-semibold uppercase tracking-wider text-gray-400">
              Behavioral hash
            </span>
          </div>
          <button
            onClick={copyHash}
            className="font-mono text-sm text-[#aa66ff] hover:text-[#cc88ff] transition-colors"
            title="Click to copy full 2048-char hash"
          >
            {hashShort}…
          </button>
          <div className="text-[10px] text-gray-600 mt-1">
            {copied ? 'copied to clipboard' : 'click to copy full hash'}
          </div>
        </div>

        {/* Claims */}
        <div className="bg-[#0a0a0f] border border-[#1e1e2e] rounded-lg p-4">
          <div className="flex items-center gap-2 mb-3">
            <Network className="w-4 h-4 text-[#3388ff]" />
            <span className="text-xs font-semibold uppercase tracking-wider text-gray-400">
              Trust claims
            </span>
          </div>
          <div className="font-mono text-lg text-[#3388ff]">{claimsTotal}</div>
          <div className="text-[10px] text-gray-500 mt-1 truncate" title={claimTypesSummary}>
            {claimTypesSummary || 'no claims yet'}
          </div>
        </div>

        {/* Cross-verification */}
        <div className="bg-[#0a0a0f] border border-[#1e1e2e] rounded-lg p-4">
          <div className="flex items-center gap-2 mb-3">
            <ShieldCheck className="w-4 h-4 text-[#00ff88]" />
            <span className="text-xs font-semibold uppercase tracking-wider text-gray-400">
              Cross-verified
            </span>
          </div>
          <div className="font-mono text-lg text-[#00ff88]">
            {(cvRatio * 100).toFixed(1)}%
          </div>
          <div className="text-[10px] text-gray-500 mt-1">
            {cvVerified} / {cvTotal} findings
          </div>
        </div>
      </div>
    </div>
  )
}
