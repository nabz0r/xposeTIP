import { useEffect, useState } from 'react'
import { Globe, MapPin, Building2, Github, ExternalLink, Shield, AlertTriangle, Link2 } from 'lucide-react'
import { getTargetProfile, getFingerprint } from '../lib/api'
import FingerprintRadar from './FingerprintRadar'
const scoreColor = (score) => {
  if (score == null) return '#666688'
  if (score >= 61) return '#ff2244'
  if (score >= 31) return '#ff8800'
  return '#00ff88'
}

const repColor = (level) => {
  if (level === 'high') return '#00ff88'
  if (level === 'medium') return '#ffcc00'
  return '#ff8800'
}

export default function ProfileHeader({ target, findings, animScore, profileData }) {
  const [localProfile, setLocalProfile] = useState(null)
  const [fingerprint, setFingerprint] = useState(null)
  const profile = profileData || localProfile

  useEffect(() => {
    if (target?.id) {
      if (!profileData) {
        getTargetProfile(target.id).then(setLocalProfile).catch(() => setLocalProfile(null))
      }
      getFingerprint(target.id).then(setFingerprint).catch(() => setFingerprint(null))
    }
  }, [target?.id, target?.last_scanned, profileData])

  // Fallback to findings-based extraction if profile not available
  const p = profile || {}
  // Never show platform names as the display name — only real names from profile data
  const rawName = p.primary_name || target.display_name || ''
  const PLATFORM_REJECT = /^(spotify|amazon|reddit|steam|keybase|github|twitter|facebook|instagram|freelancer|replit|medium|gitlab|eventbrite|lastpass|1password|bitwarden|dashlane|office365|office|unknown|admin|test|null|none|default|anonymous|noreply|support|contact)$/i
  const displayName = rawName && !PLATFORM_REJECT.test(rawName.trim()) ? rawName : ''
  const avatarUrl = p.primary_avatar || target.avatar_url || null
  const bio = p.bio || ''
  const location = p.location || ''
  const company = p.company || ''
  const title = p.title || ''
  const website = p.website || ''
  const reputation = p.reputation || null
  const emailSecurity = p.email_security || {}
  const emailProvider = p.email_provider || ''
  const socialProfiles = p.social_profiles || []
  const usernames = p.usernames || []
  const altEmails = p.emails || []
  const dataSources = p.data_sources || []

  const breachCount = p.breach_summary?.count || findings.filter(f => f.category === 'breach' && !(f.title || '').toLowerCase().includes('not configured') && !(f.title || '').toLowerCase().includes('api key')).length
  const socialCount = socialProfiles.length || findings.filter(f => f.category === 'social_account').length
  const credentialsLeaked = p.breach_summary?.credentials_leaked || false

  const threatScore = p.threat_score ?? target.threat_score ?? 0
  const exposureScore = target.exposure_score ?? 0

  const exposureColor = (s) => {
    if (s == null) return '#666688'
    if (s <= 20) return '#00ff88'
    if (s <= 40) return '#3388ff'
    if (s <= 60) return '#ffcc00'
    if (s <= 80) return '#ff8800'
    return '#ff2244'
  }
  const threatColor = (s) => {
    if (s == null) return '#666688'
    if (s <= 20) return '#00ff88'
    if (s <= 40) return '#ffcc00'
    if (s <= 60) return '#ff8800'
    return '#ff2244'
  }
  const exposureLabel = (s) => {
    if (s == null) return ''
    if (s <= 20) return 'Minimal footprint'
    if (s <= 40) return 'Low footprint'
    if (s <= 60) return 'Moderate footprint'
    if (s <= 80) return 'Wide footprint'
    return 'Maximum footprint'
  }
  const threatLabel = (s) => {
    if (s == null) return ''
    if (s <= 20) return 'Safe'
    if (s <= 40) return 'Guarded'
    if (s <= 60) return 'Elevated'
    if (s <= 80) return 'High'
    return 'Critical'
  }

  const breakdown = target.score_breakdown || p.score_breakdown || {}

  const CATEGORY_LABELS = {
    social_account: 'Social Exposure',
    breach: 'Breach Risk',
    metadata: 'Metadata Leakage',
    intelligence: 'Intelligence Findings',
    geolocation: 'Geo Exposure',
    tracking: 'Tracking',
    data_broker: 'Data Brokers',
    identity: 'Identity Intel',
    archive: 'Archive History',
  }

  return (
    <div className="bg-[#12121a] border border-[#1e1e2e] rounded-xl p-6">
      <div className="flex gap-6">
        {/* Avatar */}
        <div className="shrink-0">
          {avatarUrl ? (
            <img src={avatarUrl} alt="" className="w-20 h-20 rounded-full border-2 border-[#1e1e2e]" />
          ) : (
            <div className="w-20 h-20 rounded-full bg-[#1e1e2e] flex items-center justify-center text-2xl font-bold text-gray-500">
              {(displayName || target.email || '?')[0].toUpperCase()}
            </div>
          )}
        </div>

        {/* Info */}
        <div className="flex-1 min-w-0">
          <div className="flex items-start justify-between">
            <div>
              {!displayName && !p.identity_estimation?.gender && (
                <div className="bg-[#1e1e2e]/50 border border-[#1e1e2e] rounded-lg p-3 mb-2">
                  <p className="text-sm text-gray-400">
                    <span className="text-[#ffcc00]">Limited digital footprint.</span>
                    {' '}{socialCount > 0 ? `${socialCount} accounts detected` : 'No social accounts found'}.
                    {' '}{breachCount > 0 ? `${breachCount} breach(es) identified.` : 'No breaches found.'}
                    {' '}{emailProvider ? `Email hosted on ${emailProvider}.` : ''}
                    {' '}Scan more modules or add API keys to increase intelligence depth.
                  </p>
                </div>
              )}
              {displayName && (
                <div>
                  <div className="flex items-center gap-2">
                    <h2 className="text-xl font-semibold">{displayName}</h2>
                    {p.confidence && (
                      <span className="text-[10px] font-mono px-1.5 py-0.5 rounded-full bg-[#00ff88]/10 text-[#00ff88]">
                        {Math.round(p.confidence.overall * 100)}% confidence
                        {p.confidence.cross_verified && ' · cross-verified'}
                      </span>
                    )}
                  </div>
                  {/* Per-field confidence pills */}
                  {p.field_confidence && Object.keys(p.field_confidence).length > 0 && (
                    <div className="flex flex-wrap gap-1.5 mt-1.5">
                      {Object.entries(p.field_confidence).map(([field, fc]) => (
                        <span key={field} className="inline-flex items-center gap-1 text-[10px] font-mono px-1.5 py-0.5 rounded bg-[#1e1e2e]"
                          title={`${fc.sources?.join(', ')} — ${fc.note || ''}`}>
                          <span className="text-gray-500">{field.replace('_', ' ')}:</span>
                          <span className="text-gray-300">{fc.value}</span>
                          <span style={{
                            color: fc.confidence >= 0.7 ? '#00ff88' :
                                   fc.confidence >= 0.4 ? '#ffcc00' : '#ff8800'
                          }}>{Math.round(fc.confidence * 100)}%</span>
                          {fc.source_count > 1 && (
                            <span className="text-gray-600">({fc.source_count})</span>
                          )}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              )}
              <p className="text-sm font-mono text-gray-400">{target.email}</p>
              {title && company && <p className="text-xs text-gray-400 mt-0.5">{title} at {company}</p>}
              {bio && <p className="text-sm text-gray-300 mt-1 line-clamp-2">{bio}</p>}
              <div className="flex flex-wrap gap-3 mt-2 text-xs text-gray-400">
                {location && <span className="inline-flex items-center gap-1"><MapPin className="w-3 h-3" />{location}</span>}
                {company && !title && <span className="inline-flex items-center gap-1"><Building2 className="w-3 h-3" />{company}</span>}
                {emailProvider && <span className="inline-flex items-center gap-1"><Globe className="w-3 h-3" />{emailProvider}</span>}
                {website && (
                  <a href={website.startsWith('http') ? website : `https://${website}`} target="_blank" rel="noreferrer"
                     className="inline-flex items-center gap-1 text-[#3388ff] hover:underline">
                    <ExternalLink className="w-3 h-3" />{website.replace(/^https?:\/\//, '').substring(0, 30)}
                  </a>
                )}
                {reputation && (
                  <span className="inline-flex items-center gap-1" style={{ color: repColor(reputation.level) }}>
                    <Shield className="w-3 h-3" />Rep: {reputation.level}
                    {reputation.suspicious && <AlertTriangle className="w-3 h-3 text-[#ff2244]" />}
                  </span>
                )}
              </div>
            </div>

            {/* Fingerprint radar (replaces score donut) */}
            <div className="shrink-0">
              {fingerprint ? (
                <FingerprintRadar fingerprint={fingerprint} size="small" animate={true} />
              ) : (
                <div className="flex flex-col items-center gap-1">
                  <div className="relative w-20 h-20">
                    <svg viewBox="0 0 36 36" className="w-full h-full -rotate-90">
                      <circle cx="18" cy="18" r="15.5" fill="none" stroke="#1e1e2e" strokeWidth="3" />
                      <circle cx="18" cy="18" r="15.5" fill="none"
                        stroke={scoreColor(target.exposure_score)}
                        strokeWidth="3"
                        strokeDasharray={`${animScore} 100`}
                        strokeLinecap="round"
                        style={{ transition: 'stroke-dasharray 0.3s ease' }} />
                    </svg>
                    <div className="absolute inset-0 flex items-center justify-center">
                      <span className="text-lg font-mono font-bold" style={{ color: scoreColor(target.exposure_score) }}>
                        {target.exposure_score ?? '-'}
                      </span>
                    </div>
                  </div>
                  <span className="text-[10px] text-gray-500 uppercase tracking-wider">Exposure</span>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Social profiles strip */}
      {socialProfiles.length > 0 && (
        <div className="flex flex-wrap gap-2 mt-4 pt-3 border-t border-[#1e1e2e]">
          {socialProfiles.slice(0, 12).map((sp, i) => (
            <a key={i} href={sp.url || '#'} target="_blank" rel="noreferrer"
               className="inline-flex items-center gap-1 px-2 py-0.5 text-[11px] font-mono bg-[#1e1e2e] rounded hover:bg-[#2a2a3e] text-gray-300 transition-colors">
              <Link2 className="w-3 h-3 text-[#3388ff]" />
              {sp.platform || 'unknown'}
              {sp.username && <span className="text-gray-500">@{sp.username}</span>}
            </a>
          ))}
          {socialProfiles.length > 12 && (
            <span className="text-[11px] text-gray-500 self-center">+{socialProfiles.length - 12} more</span>
          )}
        </div>
      )}

      {/* Dual Score Gauges */}
      {(exposureScore != null || threatScore != null) && (
        <div className="flex gap-4 mt-4 pt-4 border-t border-[#1e1e2e]">
          <div className="flex-1">
            <div className="text-[10px] text-gray-500 uppercase tracking-wider mb-1">Exposure</div>
            <div className="flex items-center gap-2 mb-1">
              <span className="text-2xl font-mono font-bold" style={{ color: exposureColor(exposureScore) }}>{exposureScore}</span>
              <span className="text-[10px] text-gray-500">{exposureLabel(exposureScore)}</span>
            </div>
            <div className="h-2 bg-[#0a0a0f] rounded-full overflow-hidden">
              <div className="h-full rounded-full transition-all duration-700" style={{ width: `${exposureScore || 0}%`, backgroundColor: exposureColor(exposureScore) }} />
            </div>
          </div>
          <div className="flex-1">
            <div className="text-[10px] text-gray-500 uppercase tracking-wider mb-1">Threat</div>
            <div className="flex items-center gap-2 mb-1">
              <span className="text-2xl font-mono font-bold" style={{ color: threatColor(threatScore) }}>{threatScore}</span>
              <span className="text-[10px] text-gray-500">{threatLabel(threatScore)}</span>
            </div>
            <div className="h-2 bg-[#0a0a0f] rounded-full overflow-hidden">
              <div className="h-full rounded-full transition-all duration-700" style={{ width: `${threatScore || 0}%`, backgroundColor: threatColor(threatScore) }} />
            </div>
          </div>
        </div>
      )}

      {/* Stats bar */}
      <div className="grid grid-cols-2 sm:grid-cols-5 gap-3 mt-4 pt-4 border-t border-[#1e1e2e]">
        <div className="text-center">
          <div className="text-lg font-mono font-bold text-[#ff2244]">{breachCount}</div>
          <div className="text-[10px] text-gray-500 uppercase tracking-wider">Breaches</div>
        </div>
        <div className="text-center">
          <div className="text-lg font-mono font-bold text-[#3388ff]">{socialCount}</div>
          <div className="text-[10px] text-gray-500 uppercase tracking-wider">Accounts</div>
        </div>
        <div className="text-center">
          <div className="text-lg font-mono font-bold" style={{ color: credentialsLeaked ? '#ff2244' : '#00ff88' }}>
            {credentialsLeaked ? 'YES' : 'NO'}
          </div>
          <div className="text-[10px] text-gray-500 uppercase tracking-wider">Creds Leaked</div>
        </div>
        <div className="text-center">
          <div className="text-lg font-mono font-bold text-[#ffcc00]">{findings.length}</div>
          <div className="text-[10px] text-gray-500 uppercase tracking-wider">Total Findings</div>
        </div>
        <div className="text-center">
          <div className="text-lg font-mono font-bold text-[#666688]">{dataSources.length}</div>
          <div className="text-[10px] text-gray-500 uppercase tracking-wider">Sources</div>
        </div>
      </div>

      {/* Email security badge */}
      {emailSecurity.security_level && (
        <div className="mt-3 flex items-center gap-2 text-xs">
          <span className="text-gray-500">Email Security:</span>
          <span className={`px-2 py-0.5 rounded font-mono ${
            emailSecurity.security_level === 'strong' ? 'bg-[#00ff88]/15 text-[#00ff88]' :
            emailSecurity.security_level === 'moderate' ? 'bg-[#ffcc00]/15 text-[#ffcc00]' :
            'bg-[#ff2244]/15 text-[#ff2244]'
          }`}>{emailSecurity.security_level}</span>
          <span className="text-gray-600">
            SPF:{emailSecurity.spf ? '✓' : '✗'} DMARC:{emailSecurity.dmarc ? '✓' : '✗'} DKIM:{emailSecurity.dkim ? '✓' : '✗'}
          </span>
        </div>
      )}

      {/* Score breakdown bars */}
      {Object.keys(breakdown).length > 0 && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mt-4 pt-4 border-t border-[#1e1e2e]">
          {Object.entries(breakdown).sort((a, b) => b[1] - a[1]).map(([cat, score]) => (
            <div key={cat} className="space-y-1">
              <div className="flex justify-between text-xs">
                <span className="text-gray-400">{CATEGORY_LABELS[cat] || cat.replace(/_/g, ' ')}</span>
                <span className="font-mono text-gray-300">{score}</span>
              </div>
              <div className="h-1.5 bg-[#1e1e2e] rounded-full overflow-hidden">
                <div className="h-full rounded-full transition-all duration-500"
                  style={{ width: `${score}%`, backgroundColor: score >= 60 ? '#ff2244' : score >= 30 ? '#ff8800' : '#00ff88' }} />
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
