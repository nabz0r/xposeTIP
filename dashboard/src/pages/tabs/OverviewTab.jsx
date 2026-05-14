import React, { useMemo } from 'react'
import { Shield, AlertTriangle, Globe, Radar, Search, Clock, MapPin } from 'lucide-react'
import FingerprintRadar, { FingerprintTimeline } from '../../components/FingerprintRadar'
import PlatformIcon from '../../components/PlatformIcon'
import IdentityCard from '../../components/IdentityCard'
import PersonaCard from '../../components/PersonaCard'
import GenerativeAvatar from '../../components/GenerativeAvatar'
import LifeTimeline from '../../components/LifeTimeline'
import RiskSignalsBlock from '../../components/RiskSignalsBlock'

const severityColors = {
  critical: '#ff2244', high: '#ff8800', medium: '#ffcc00', low: '#3388ff', info: '#666688',
}

const scoreColor = (score) => {
  if (score == null) return '#666688'
  if (score >= 61) return '#ff2244'
  if (score >= 31) return '#ff8800'
  return '#00ff88'
}

function DeepScanActivity({ findings }) {
  const stats = useMemo(() => {
    const deepFindings = findings.filter(f => f.data?.pass === 'deep')
    if (!deepFindings.length) return null

    const sources = new Set(deepFindings.map(f => f.data?.source_username).filter(Boolean))
    const types = new Set(deepFindings.map(f => f.indicator_type).filter(Boolean))
    const latest = deepFindings.reduce((best, f) => {
      if (!best || (f.created_at && f.created_at > best)) return f.created_at
      return best
    }, null)

    return {
      scanCount: sources.size,
      findingCount: deepFindings.length,
      types: [...types],
      latestDate: latest ? new Date(latest).toLocaleString('en-US', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' }) : null,
    }
  }, [findings])

  if (!stats) return null

  return (
    <div className="bg-[#12121a] border border-[#1e1e2e] rounded-xl p-4">
      <div className="flex items-center gap-2 mb-3">
        <Search className="w-4 h-4 text-[#3388ff]" />
        <h3 className="text-xs font-semibold uppercase tracking-wider text-gray-500">Deep Scan Activity</h3>
      </div>
      <div className="flex items-center gap-4 text-xs text-gray-400">
        <span>
          <span className="text-white font-semibold font-mono">{stats.scanCount}</span> deep scan{stats.scanCount !== 1 ? 's' : ''} completed
        </span>
        <span className="text-gray-600">|</span>
        <span>
          <span className="text-white font-semibold font-mono">{stats.findingCount}</span> finding{stats.findingCount !== 1 ? 's' : ''} discovered
        </span>
        {stats.types.length > 0 && (
          <>
            <span className="text-gray-600">|</span>
            <span className="font-mono text-[#3388ff]">{stats.types.join(', ')}</span>
          </>
        )}
        {stats.latestDate && (
          <>
            <span className="text-gray-600">|</span>
            <span>Last: {stats.latestDate}</span>
          </>
        )}
      </div>
    </div>
  )
}

export default function OverviewTab({ target, findings, profile, fingerprint, fpHistory, sourcesData, socialFindings, breachFindings, geoFindings, riskAssessment, remediations, criticalCount, setActiveTab, setShowScanModal, onRiskSignalViewAll }) {
  return (
    <div className="space-y-4">
      {/* Email deliverability banner — only show for genuinely bad emails */}
      {profile?.email_status && typeof profile.email_status === 'object' && profile.email_status.deliverable === false && (
        <div className="bg-[#332800] border border-[#665500] rounded-xl p-4 flex items-center gap-3">
          <AlertTriangle className="w-5 h-5 text-[#ffcc00] shrink-0" />
          <div>
            <p className="text-[#ffcc00] text-sm font-semibold">
              {profile.email_status.suspicious ? 'Suspicious email detected' : 'Inactive or non-existent email'}
            </p>
            <p className="text-gray-400 text-xs mt-1">
              This email appears inactive or undeliverable. Results below are based on historical data and username analysis.
            </p>
          </div>
        </div>
      )}

      {/* Risk Dashboard */}
      {riskAssessment && (
        <div className={`rounded-xl p-5 border ${
          riskAssessment.data?.risk_level === 'CRITICAL' ? 'bg-[#ff2244]/10 border-[#ff2244]/30' :
          riskAssessment.data?.risk_level === 'HIGH' ? 'bg-[#ff8800]/10 border-[#ff8800]/30' :
          riskAssessment.data?.risk_level === 'MODERATE' ? 'bg-[#ffcc00]/10 border-[#ffcc00]/30' :
          'bg-[#00ff88]/10 border-[#00ff88]/30'
        }`}>
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-3">
              <Shield className={`w-6 h-6 ${
                riskAssessment.data?.risk_level === 'CRITICAL' ? 'text-[#ff2244]' :
                riskAssessment.data?.risk_level === 'HIGH' ? 'text-[#ff8800]' :
                riskAssessment.data?.risk_level === 'MODERATE' ? 'text-[#ffcc00]' :
                'text-[#00ff88]'
              }`} />
              <div>
                <h3 className="text-sm font-semibold">RISK LEVEL: {riskAssessment.data?.risk_level}</h3>
                <p className="text-xs text-gray-400">{riskAssessment.data?.summary || {
                  CRITICAL: 'This identity is severely compromised. Immediate action required.',
                  HIGH: 'Significant exposure detected. Multiple risks need attention.',
                  MODERATE: 'Some exposure found. Recommended improvements available.',
                  LOW: 'Minimal exposure. Good digital hygiene.',
                }[riskAssessment.data?.risk_level] || ''}</p>
              </div>
            </div>
            <div className="flex gap-4 text-right">
              <div>
                <div className="text-2xl font-mono font-bold" style={{ color: scoreColor(target.exposure_score) }}>
                  {target.exposure_score ?? '-'}
                </div>
                <div className="text-[10px] text-gray-500 uppercase">Exposure</div>
              </div>
              <div>
                <div className="text-2xl font-mono font-bold" style={{ color: (target.threat_score ?? 0) >= 61 ? '#ff2244' : (target.threat_score ?? 0) >= 31 ? '#ff8800' : '#00ff88' }}>
                  {target.threat_score ?? 0}
                </div>
                <div className="text-[10px] text-gray-500 uppercase">Threat</div>
              </div>
            </div>
          </div>
          {/* Progress bar */}
          <div className="h-2 bg-[#0a0a0f] rounded-full overflow-hidden mb-4">
            <div className="h-full rounded-full transition-all duration-1000"
              style={{ width: `${target.exposure_score || 0}%`, backgroundColor: scoreColor(target.exposure_score) }} />
          </div>
          {/* Stat pills */}
          <div className="flex gap-3 mb-4">
            {[
              { label: 'Accounts', value: socialFindings.length, color: '#3388ff' },
              { label: 'Breaches', value: breachFindings.length, color: '#ff2244' },
              { label: 'Findings', value: findings.length, color: '#ffcc00' },
              { label: 'Sources', value: sourcesData?.sources?.length || 0, color: '#666688' },
            ].map(s => (
              <div key={s.label} className="flex-1 bg-[#0a0a0f] rounded-lg p-3 text-center">
                <div className="text-lg font-mono font-bold" style={{ color: s.color }}>{s.value}</div>
                <div className="text-[10px] text-gray-500 uppercase">{s.label}</div>
              </div>
            ))}
          </div>
          {/* Executive Summary */}
          {riskAssessment?.data?.executive_summary && (
            <div className="bg-[#0a0a0f] rounded-lg p-4 mt-4">
              <h4 className="text-[10px] uppercase tracking-wider text-gray-500 mb-2">Executive Summary</h4>
              <p className="text-sm text-gray-300 leading-relaxed">{riskAssessment.data.executive_summary}</p>
            </div>
          )}
        </div>
      )}

      {/* Identity Estimation */}
      <IdentityCard profile={profile} />

      {/* Life Timeline — chronological digital history */}
      {profile?.life_timeline?.length > 0 && (
        <div className="bg-[#12121a] border border-[#1e1e2e] rounded-xl p-5">
          <h3 className="text-xs font-semibold uppercase tracking-wider text-gray-500 mb-4">Digital Life Timeline</h3>
          <LifeTimeline events={profile.life_timeline} compact={false} />
        </div>
      )}

      {/* Persona Clusters */}
      <PersonaCard personas={profile?.personas} />

      {/* Timezone Intelligence */}
      {profile?.timezone && profile.timezone.confidence >= 0.4 && (
        <div className="bg-[#12121a] border border-[#1e1e2e] rounded-xl p-4">
          <div className="flex items-center gap-2">
            <Clock className="w-4 h-4 text-[#ffcc00]" />
            <span className="text-xs font-semibold uppercase tracking-wider text-gray-500">Timezone Intelligence</span>
          </div>
          <div className="flex items-center gap-4 mt-2 text-xs text-gray-400">
            <span className="text-white font-mono font-semibold">
              UTC{profile.timezone.utc_offset >= 0 ? '+' : ''}{profile.timezone.utc_offset}
            </span>
            <span>{profile.timezone.regions?.[0]}</span>
            <span className="text-gray-600">|</span>
            <span>{Math.round(profile.timezone.confidence * 100)}% confidence</span>
            <span className="text-gray-600">|</span>
            <span>{profile.timezone.sample_count} timestamps analyzed</span>
          </div>
        </div>
      )}

      {/* Geographic Intelligence */}
      {profile?.geo_consistency && profile.geo_consistency.primary_country && (
        <div className="bg-[#12121a] border border-[#1e1e2e] rounded-xl p-4">
          <div className="flex items-center gap-2 mb-2">
            <MapPin className="w-4 h-4 text-[#00ff88]" />
            <span className="text-xs font-semibold uppercase tracking-wider text-gray-500">Geographic Intelligence</span>
            <span className={`text-[10px] px-1.5 py-0.5 rounded font-mono ${
              profile.geo_consistency.consistency_score >= 0.8 ? 'bg-[#00ff88]/15 text-[#00ff88]' :
              profile.geo_consistency.consistency_score >= 0.5 ? 'bg-[#ffcc00]/15 text-[#ffcc00]' :
              'bg-[#ff2244]/15 text-[#ff2244]'
            }`}>
              {Math.round(profile.geo_consistency.consistency_score * 100)}% consistent
            </span>
          </div>
          <p className="text-xs text-gray-400 mb-2">{profile.geo_consistency.verdict}</p>
          <div className="flex flex-wrap gap-1.5">
            {Object.entries(profile.geo_consistency.country_votes || {}).slice(0, 5).map(([cc, score]) => (
              <span key={cc} className="text-[10px] bg-[#0a0a0f] border border-[#1e1e2e] px-2 py-0.5 rounded font-mono text-gray-300">
                {cc} <span className="text-gray-600">({typeof score === 'number' ? score.toFixed(1) : score})</span>
              </span>
            ))}
          </div>
          {profile.geo_consistency.anomalies?.length > 0 && (
            <p className="mt-2 text-[10px] text-[#ffcc00]/70">
              {profile.geo_consistency.anomalies.length} anomal{profile.geo_consistency.anomalies.length === 1 ? 'y' : 'ies'} detected
            </p>
          )}
        </div>
      )}

      {/* Deep Scan Activity */}
      <DeepScanActivity findings={findings} />

      {/* Digital Fingerprint */}
      {fingerprint && (
        <div className="bg-[#12121a] border border-[#1e1e2e] rounded-xl p-5">
          <h3 className="text-xs font-semibold uppercase tracking-wider text-gray-500 mb-4">Digital Fingerprint</h3>
          <div className="flex flex-col lg:flex-row items-center gap-6">
            {/* GenerativeAvatar — identity glyph from graph topology */}
            {fingerprint?.avatar_seed && (
              <div className="shrink-0 flex flex-col items-center gap-2">
                <GenerativeAvatar seed={fingerprint.avatar_seed} size={120} score={target?.exposure_score} />
                <span className="text-[10px] text-gray-600 font-mono">identity glyph</span>
              </div>
            )}
            <div className="flex-1 flex justify-center">
              <FingerprintRadar fingerprint={fingerprint} size="large" animate={true} />
            </div>
            <div className="w-full lg:w-64 space-y-2">
              {Object.entries(fingerprint.axes || {}).map(([key, val]) => {
                const rawKey = key === 'email_age' ? 'email_age_years' : key === 'security' ? 'security_weak' : key
                const rawVal = fingerprint.raw_values?.[rawKey] ?? 0
                return (
                  <div key={key} className="space-y-0.5">
                    <div className="flex justify-between text-[10px]">
                      <span className="text-gray-400">{key.replace(/_/g, ' ')}</span>
                      <span className="font-mono" style={{ color: fingerprint.color }}>{rawVal}</span>
                    </div>
                    <div className="h-1.5 bg-[#0a0a0f] rounded-full overflow-hidden">
                      <div className="h-full rounded-full transition-all duration-700"
                        style={{ width: `${(val * 100).toFixed(0)}%`, backgroundColor: fingerprint.color }} />
                    </div>
                  </div>
                )
              })}
            </div>
          </div>
        </div>
      )}

      {/* Fingerprint Evolution */}
      {fpHistory.length > 1 && (
        <div className="bg-[#12121a] border border-[#1e1e2e] rounded-xl p-5">
          <FingerprintTimeline snapshots={fpHistory} />
        </div>
      )}

      {/* Remediation Actions */}
      {remediations.length > 0 && (
        <div>
          <h3 className="text-xs font-semibold uppercase tracking-wider text-gray-500 mb-3">
            Top Actions Required ({remediations.length})
          </h3>
          <div className="space-y-2">
            {remediations.slice(0, 7).map((r, i) => (
              <div key={i} className="bg-[#12121a] border border-[#1e1e2e] rounded-lg p-3 hover:border-[#00ff88]/20 transition-colors">
                <div className="flex items-start gap-3">
                  <span className={`inline-block text-[10px] font-bold px-1.5 py-0.5 rounded-full mt-0.5 ${
                    r.priority === 'critical' ? 'bg-[#ff2244]/20 text-[#ff2244]' :
                    r.priority === 'high' ? 'bg-[#ff8800]/20 text-[#ff8800]' :
                    'bg-[#ffcc00]/20 text-[#ffcc00]'
                  }`}>{i + 1}</span>
                  <div className="flex-1 min-w-0">
                    <div className="text-sm font-medium">{r.action}</div>
                    {r.finding && <p className="text-[10px] text-gray-500 mt-0.5">{r.finding}</p>}
                    {r.steps && (
                      <div className="flex flex-wrap gap-1 mt-1.5">
                        {r.steps.slice(0, 3).map((step, j) => (
                          <span key={j} className="text-[10px] px-1.5 py-0.5 rounded bg-[#1e1e2e] text-gray-400">{step}</span>
                        ))}
                      </div>
                    )}
                  </div>
                  {r.link && (
                    <a href={r.link} target="_blank" rel="noreferrer"
                       className="text-[10px] px-2 py-1 rounded bg-[#00ff88]/10 text-[#00ff88] hover:bg-[#00ff88]/20 shrink-0">
                      Secure
                    </a>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Critical alerts (fallback when no risk assessment yet) */}
      {!riskAssessment && criticalCount > 0 && (
        <div className="bg-[#ff2244]/10 border border-[#ff2244]/30 rounded-xl p-4 flex items-start gap-3">
          <AlertTriangle className="w-5 h-5 text-[#ff2244] shrink-0 mt-0.5" />
          <div>
            <h3 className="text-sm font-semibold text-[#ff2244]">{criticalCount} Critical/High findings</h3>
            <p className="text-xs text-gray-400 mt-1">This identity has severe exposure requiring immediate attention.</p>
          </div>
        </div>
      )}

      {/* Risk Signals (phone / crypto / legal — secondary indicators) */}
      <RiskSignalsBlock findings={findings} onViewAll={onRiskSignalViewAll} />

      {/* Breach summary cards — moved to dedicated Breaches tab */}
      {breachFindings.length > 0 && (
        <div className="flex items-center gap-2">
          <span className="text-xs text-gray-500">{breachFindings.length} breach{breachFindings.length !== 1 ? 'es' : ''} detected</span>
          <button onClick={() => setActiveTab('breaches')} className="text-xs text-[#3388ff] hover:underline">
            View details
          </button>
        </div>
      )}

      {/* Social accounts with PlatformIcon */}
      {socialFindings.length > 0 && (
        <div>
          <h3 className="text-xs font-semibold uppercase tracking-wider text-gray-500 mb-3">Accounts ({socialFindings.length})</h3>
          <div className="flex flex-wrap gap-2">
            {socialFindings.slice(0, 15).map(f => {
              const platform = f.data?.platform || f.data?.network || f.data?.service || f.title?.split(' on ')?.[1] || f.module
              const username = f.data?.username || f.data?.handle || f.data?.login || ''
              return (
                <PlatformIcon key={f.id} platform={platform} username={username} url={f.url} />
              )
            })}
            {socialFindings.length > 15 && (
              <button onClick={() => setActiveTab('findings')} className="text-xs text-gray-500 self-center ml-1">
                +{socialFindings.length - 15} more
              </button>
            )}
          </div>
        </div>
      )}

      {/* Geo summary */}
      {geoFindings.length > 0 && (
        <div>
          <h3 className="text-xs font-semibold uppercase tracking-wider text-gray-500 mb-3">Mail Server Locations</h3>
          <p className="text-[10px] text-gray-600 mb-2">These are mail server locations, not the user's physical location.</p>
          <div className="flex flex-wrap gap-2">
            {geoFindings.map(f => (
              <span key={f.id} className="inline-flex items-center gap-1.5 text-xs px-2.5 py-1.5 rounded-lg bg-[#12121a] border border-[#1e1e2e]">
                <Globe className="w-3 h-3 text-[#3388ff]" />
                {f.data?.city}, {f.data?.country}
                <span className="text-gray-500">({f.data?.ip})</span>
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Source reliability — moved to dedicated Sources tab */}
      {sourcesData?.sources?.length > 0 && (
        <div className="flex items-center gap-2">
          <span className="text-xs text-gray-500">{sourcesData.sources.length} intelligence sources</span>
          <button onClick={() => setActiveTab('sources')} className="text-xs text-[#3388ff] hover:underline">
            View details
          </button>
        </div>
      )}

      {/* Empty state */}
      {findings.length === 0 && (
        <div className="bg-[#12121a] border border-[#1e1e2e] rounded-xl p-12 text-center">
          <Shield className="w-12 h-12 text-gray-600 mx-auto mb-3" />
          <h3 className="text-lg font-medium text-gray-300">No intelligence yet</h3>
          <p className="text-sm text-gray-500 mt-1 mb-4">Launch a scan to discover this identity's digital exposure.</p>
          <button onClick={() => setShowScanModal(true)}
            className="inline-flex items-center gap-2 bg-[#00ff88] text-black font-semibold rounded-lg px-6 py-2.5 text-sm hover:bg-[#00ff88]/90">
            <Radar className="w-4 h-4" /> Launch First Scan
          </button>
        </div>
      )}
    </div>
  )
}
