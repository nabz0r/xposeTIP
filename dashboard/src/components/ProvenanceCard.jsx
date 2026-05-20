import React from 'react'
import { ExternalLink, ShieldCheck, ShieldAlert, Check, Link as LinkIcon, AlertTriangle, Info } from 'lucide-react'
import { tierStyle, confidenceColor, relativeTime, confidenceBreakdown } from '../lib/findingProvenance'

/**
 * S124 — Verified provenance card.
 * Renders below the description in an expanded Findings row.
 * Shows source + tier + reliability, verification status, confidence with breakdown,
 * timeline (first/last seen), and source link.
 */
export default function ProvenanceCard({ finding: f }) {
  if (!f) return null
  const tier = f.reliability_tier || 'LOW'
  const t = tierStyle(tier)
  const isHoldover = (f.severity === 'low' && /manual.check|verify manually|search for/i.test(f.title || ''))
  const accentColor = isHoldover ? '#ff8800' : (tier === 'HIGH' ? '#00ff88' : tier === 'MEDIUM' ? '#ffcc00' : '#ff8800')
  const HeaderIcon = isHoldover ? ShieldAlert : ShieldCheck
  const headerLabel = isHoldover ? 'PROVENANCE — MANUAL CHECK REQUIRED' : 'PROVENANCE'
  const confColor = confidenceColor(f.confidence)
  const conf = f.confidence != null ? Math.round(f.confidence * 100) + '%' : '—'
  const firstSeen = relativeTime(f.first_seen)
  const lastSeen = relativeTime(f.last_seen)
  const sameTime = firstSeen === lastSeen
  const peers = f.cross_verified_by || []

  return (
    <div
      className="bg-[#12121a] border border-[#1e1e2e] px-4 py-3.5 mb-3"
      style={{ borderLeftWidth: '2px', borderLeftColor: accentColor, borderRadius: 0 }}
    >
      <div className="flex items-center gap-2 mb-3">
        <HeaderIcon className="w-3.5 h-3.5" style={{ color: accentColor }} />
        <span className="font-mono text-[10px] font-medium tracking-widest" style={{ color: accentColor }}>
          {headerLabel}
        </span>
      </div>

      <div className="grid gap-y-2 gap-x-4 text-xs" style={{ gridTemplateColumns: '110px 1fr' }}>

        {/* Source */}
        <span className="text-gray-500">Source</span>
        <span className="flex items-center flex-wrap gap-2">
          <span className="font-mono text-gray-200">{f.module}</span>
          <span
            className="font-mono text-[10px] px-1.5 py-px rounded"
            style={{ backgroundColor: t.bg, color: t.fg }}
          >
            {t.label} · {f.source_reliability != null ? Math.round(f.source_reliability * 100) + '%' : '—'}
          </span>
          {f.reliability_label && (
            <span title={f.reliability_label} className="text-gray-600">
              <Info className="w-3 h-3 inline-block" />
            </span>
          )}
        </span>

        {/* Verification */}
        <span className="text-gray-500">Verification</span>
        <span className="text-gray-300">
          {f.verified ? (
            <>
              <Check className="w-3 h-3 inline-block mr-1" style={{ color: '#00ff88' }} />
              <span style={{ color: '#00ff88' }}>Verified</span>
            </>
          ) : isHoldover ? (
            <>
              <AlertTriangle className="w-3 h-3 inline-block mr-1" style={{ color: '#ff8800' }} />
              <span style={{ color: '#ff8800' }}>Not verified — placeholder hit, open link to confirm</span>
            </>
          ) : (
            <span className="text-gray-500">Not verified</span>
          )}

          {f.cross_verified_count > 0 && (
            <>
              <span className="text-gray-700 mx-2">·</span>
              <LinkIcon className="w-3 h-3 inline-block mr-1" style={{ color: '#3388ff' }} />
              <span style={{ color: '#3388ff' }}>
                Cross-verified by {f.cross_verified_count} source{f.cross_verified_count > 1 ? 's' : ''}
              </span>
              {peers.length > 0 && (
                <span className="text-gray-600 text-[11px] ml-1.5">
                  ({peers.slice(0, 3).join(', ')}{peers.length > 3 ? `, +${peers.length - 3}` : ''})
                </span>
              )}
            </>
          )}
        </span>

        {/* Confidence */}
        <span className="text-gray-500">Confidence</span>
        <span>
          <span className="font-mono font-medium" style={{ color: confColor, fontSize: '13px' }}>{conf}</span>
          <span className="text-gray-500 text-[11px] ml-2.5">{confidenceBreakdown(f)}</span>
        </span>

        {/* Timeline */}
        {(firstSeen || lastSeen) && (
          <>
            <span className="text-gray-500">Timeline</span>
            <span className="text-gray-300">
              {firstSeen && <>First seen <span className="font-mono text-gray-200">{firstSeen}</span></>}
              {!sameTime && lastSeen && (
                <>
                  <span className="text-gray-700 mx-2">·</span>
                  Last seen <span className="font-mono text-gray-200">{lastSeen}</span>
                </>
              )}
            </span>
          </>
        )}

        {/* Source link */}
        {f.url && (
          <>
            <span className="text-gray-500">Source link</span>
            <span>
              <a
                href={f.url}
                target="_blank"
                rel="noreferrer"
                className="text-[#3388ff] hover:underline font-mono text-[11px] inline-flex items-center gap-1"
              >
                {f.url.replace(/^https?:\/\//, '').slice(0, 80)}
                <ExternalLink className="w-3 h-3" />
              </a>
            </span>
          </>
        )}

      </div>
    </div>
  )
}
