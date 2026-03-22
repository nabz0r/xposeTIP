import React, { Fragment } from 'react'
import { ChevronDown, ChevronRight, ExternalLink, Shield, Globe } from 'lucide-react'

const severityColors = {
  critical: '#ff2244', high: '#ff8800', medium: '#ffcc00', low: '#3388ff', info: '#666688',
}
const severityOrder = ['critical', 'high', 'medium', 'low', 'info']

const SECURITY_URLS = {
  spotify: 'https://www.spotify.com/account/security/',
  twitter: 'https://twitter.com/settings/security',
  facebook: 'https://www.facebook.com/settings?tab=security',
  instagram: 'https://www.instagram.com/accounts/privacy_and_security/',
  github: 'https://github.com/settings/security',
  google: 'https://myaccount.google.com/security',
  reddit: 'https://www.reddit.com/prefs/update/',
  steam: 'https://store.steampowered.com/account/',
  linkedin: 'https://www.linkedin.com/psettings/',
  discord: 'https://discord.com/channels/@me',
  twitch: 'https://www.twitch.tv/settings/security',
  medium: 'https://medium.com/me/settings/security',
  gitlab: 'https://gitlab.com/-/profile/account',
}

const DATA_CLASS_COLORS = {
  'Passwords': '#ff2244',
  'Email addresses': '#ff8800',
  'Phone numbers': '#ffcc00',
  'IP addresses': '#ff8800',
  'Credit cards': '#ff2244',
  'Physical addresses': '#ff8800',
}

function FindingDataCard({ finding }) {
  const d = finding.data || {}
  const mod = finding.module

  // Breach findings (HIBP, leaked_domains)
  if (finding.category === 'breach' && (d.Name || d.breach_name)) {
    const name = d.Name || d.breach_name
    const date = d.BreachDate || d.date || ''
    const dataClasses = d.DataClasses || d.data_classes || []
    const count = d.PwnCount || d.records || ''
    const hasPasswords = dataClasses.some(dc => dc.toLowerCase().includes('password'))
    return (
      <div className="bg-[#12121a] rounded-lg p-4 border border-[#ff2244]/20">
        <div className="flex items-center gap-2 mb-2">
          <Shield className="w-4 h-4 text-[#ff2244]" />
          <span className="font-semibold text-sm">{name}</span>
          {date && <span className="text-xs text-gray-500">{date}</span>}
        </div>
        {count && <p className="text-xs text-gray-400 mb-2">{typeof count === 'number' ? count.toLocaleString() : count} records exposed</p>}
        {dataClasses.length > 0 && (
          <div className="flex flex-wrap gap-1 mb-3">
            {dataClasses.slice(0, 12).map(dc => (
              <span key={dc} className="text-[10px] px-1.5 py-0.5 rounded font-mono"
                style={{ backgroundColor: (DATA_CLASS_COLORS[dc] || '#666688') + '15', color: DATA_CLASS_COLORS[dc] || '#ff8800' }}>
                {dc}
              </span>
            ))}
            {dataClasses.length > 12 && <span className="text-[10px] text-gray-500">+{dataClasses.length - 12}</span>}
          </div>
        )}
        {hasPasswords && (
          <div className="text-xs text-[#ff2244] bg-[#ff2244]/10 rounded px-2 py-1.5">
            ⚠ Passwords were exposed in this breach — change your password immediately
          </div>
        )}
      </div>
    )
  }

  // Social account findings
  if (finding.category === 'social_account' && (d.platform || d.network || d.service)) {
    const platform = d.platform || d.network || d.service || ''
    const username = d.username || d.handle || d.login || ''
    const url = finding.url || d.url || ''
    const secUrl = SECURITY_URLS[platform.toLowerCase()] || null
    return (
      <div className="bg-[#12121a] rounded-lg p-4 border border-[#3388ff]/20">
        <div className="flex items-center gap-3">
          {d.avatar_url && <img src={d.avatar_url} alt="" className="w-8 h-8 rounded-full" />}
          <div className="flex-1 min-w-0">
            <span className="text-sm font-medium">{platform}</span>
            {username && <span className="text-xs text-gray-400 ml-2">@{username}</span>}
            {url && <a href={url} target="_blank" rel="noreferrer" className="block text-[10px] text-[#3388ff] hover:underline mt-0.5">{url.replace(/https?:\/\//, '').substring(0, 50)}</a>}
          </div>
          {secUrl && (
            <a href={secUrl} target="_blank" rel="noreferrer"
               className="text-[10px] px-2 py-1 rounded bg-[#00ff88]/10 text-[#00ff88] hover:bg-[#00ff88]/20 whitespace-nowrap">
              Secure this account →
            </a>
          )}
        </div>
      </div>
    )
  }

  // EmailRep reputation
  if (mod === 'emailrep' && d.reputation) {
    const repColor = d.reputation === 'high' ? '#00ff88' : d.reputation === 'medium' ? '#ffcc00' : '#ff8800'
    return (
      <div className="bg-[#12121a] rounded-lg p-3 border border-[#1e1e2e] grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
        <div><span className="text-gray-500">Reputation</span><div className="font-mono font-semibold" style={{ color: repColor }}>{d.reputation}</div></div>
        <div><span className="text-gray-500">Suspicious</span><div className="font-mono">{d.suspicious ? 'Yes' : 'No'}</div></div>
        {d.first_seen && <div><span className="text-gray-500">First seen</span><div className="font-mono">{d.first_seen}</div></div>}
        {d.domain_age_days != null && <div><span className="text-gray-500">Domain age</span><div className="font-mono">{d.domain_age_days}d</div></div>}
      </div>
    )
  }

  // GitHub deep
  if (mod === 'github_deep' && d.login) {
    return (
      <div className="bg-[#12121a] rounded-lg p-3 border border-[#1e1e2e] flex items-start gap-3">
        {d.avatar_url && <img src={d.avatar_url} alt="" className="w-10 h-10 rounded-full" />}
        <div className="text-xs space-y-1">
          <div className="font-semibold text-sm">{d.name || d.login}</div>
          {d.bio && <p className="text-gray-400 line-clamp-2">{d.bio}</p>}
          <div className="flex gap-3 text-gray-500">
            {d.public_repos != null && <span>{d.public_repos} repos</span>}
            {d.followers != null && <span>{d.followers} followers</span>}
            {d.company && <span>{d.company}</span>}
            {d.location && <span>{d.location}</span>}
          </div>
        </div>
      </div>
    )
  }

  // Managed domain (from domain_analyzer)
  if (d.analyzer === 'domain_analyzer' && d.managed) {
    return (
      <div className="bg-[#12121a] rounded-lg p-3 border border-[#3388ff]/20">
        <div className="flex items-center gap-2">
          <Globe className="w-4 h-4 text-[#3388ff]" />
          <span className="text-sm font-medium text-[#3388ff]">Managed Domain</span>
        </div>
        <p className="text-xs text-gray-400 mt-1">{d.domain} is a SaaS email provider. DNS records are managed by the provider — no user action needed.</p>
      </div>
    )
  }

  if (mod === 'dns_deep' && (d.spf_record !== undefined || d.security_score !== undefined)) {
    if (d.security_score !== undefined) {
      return (
        <div className="bg-[#12121a] rounded-lg p-3 border border-[#1e1e2e]">
          <div className="grid grid-cols-3 gap-3 text-xs mb-2">
            <div><span className="text-gray-500">SPF</span><div className={d.has_spf ? 'text-[#00ff88]' : 'text-[#ff2244]'}>{d.has_spf ? '✓ Configured' : '✗ Missing'}</div></div>
            <div><span className="text-gray-500">DMARC</span><div className={d.has_dmarc ? 'text-[#00ff88]' : 'text-[#ff2244]'}>{d.has_dmarc ? '✓ Configured' : '✗ Missing'}</div></div>
            <div><span className="text-gray-500">DKIM</span><div className={d.has_dkim ? 'text-[#00ff88]' : 'text-[#ffcc00]'}>{d.has_dkim ? '✓ Configured' : '⚠ Not found'}</div></div>
          </div>
          {d.spf_record && <div className="text-[10px] font-mono text-gray-500 bg-[#0a0a0f] p-2 rounded mt-2 break-all">{d.spf_record}</div>}
          {d.dmarc_record && <div className="text-[10px] font-mono text-gray-500 bg-[#0a0a0f] p-2 rounded mt-1 break-all">{d.dmarc_record}</div>}
        </div>
      )
    }
  }

  // Intelligence findings
  if (mod === 'intelligence' && d.risk_level) {
    return (
      <div className="bg-[#12121a] rounded-lg p-3 border border-[#1e1e2e]">
        {d.summary && <p className="text-xs text-gray-300 mb-2">{d.summary}</p>}
        {d.correlations?.length > 0 && (
          <div className="space-y-1 mb-2">
            {d.correlations.slice(0, 5).map((c, i) => (
              <div key={i} className="text-[10px] text-gray-400 flex items-center gap-1">
                <span className="text-[#3388ff]">→</span> {c}
              </div>
            ))}
          </div>
        )}
      </div>
    )
  }

  // Scraper engine findings
  if (mod === 'scraper_engine' && d.scraper_name) {
    return (
      <div className="bg-[#12121a] rounded-lg p-3 border border-[#1e1e2e]">
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs font-mono text-gray-400">Source: {d.scraper_name}</span>
        </div>
        {d.extracted && Object.keys(d.extracted).length > 0 && (
          <div className="grid grid-cols-2 gap-2 text-xs">
            {Object.entries(d.extracted).map(([k, v]) => (
              <div key={k}><span className="text-gray-500">{k}</span><div className="font-mono text-gray-300 truncate">{String(v)}</div></div>
            ))}
          </div>
        )}
      </div>
    )
  }

  // Geolocation
  if (finding.category === 'geolocation' && (d.lat || d.latitude)) {
    return (
      <div className="bg-[#12121a] rounded-lg p-3 border border-[#1e1e2e]">
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs mb-2">
          {d.city && <div><span className="text-gray-500">City</span><div className="font-mono">{d.city}</div></div>}
          {d.country && <div><span className="text-gray-500">Country</span><div className="font-mono">{d.country}</div></div>}
          {d.isp && <div><span className="text-gray-500">ISP</span><div className="font-mono">{d.isp}</div></div>}
          {(d.as || d.org) && <div><span className="text-gray-500">ASN</span><div className="font-mono truncate">{d.as || d.org}</div></div>}
        </div>
        <div className="text-[10px] text-gray-600 italic">This is the mail server location, not the user's physical location.</div>
      </div>
    )
  }

  return null
}

export default function FindingsTab({ target, findings, filteredFindings, expanded, setExpanded, sevFilter, setSevFilter, modFilter, setModFilter, statusFilter, setStatusFilter, findingsLimit, setFindingsLimit, uniqueModules, load, patchFinding }) {
  return (
    <div>
      {/* Remediation progress bar */}
      {(() => {
        const actionable = findings.filter(f => ['critical', 'high', 'medium'].includes(f.severity))
        const resolved = actionable.filter(f => ['resolved', 'dismissed', 'false_positive'].includes(f.status))
        const pct = actionable.length > 0 ? Math.round(resolved.length / actionable.length * 100) : 100
        const barColor = pct >= 80 ? '#00ff88' : pct >= 50 ? '#ffcc00' : '#ff8800'
        return actionable.length > 0 ? (
          <div className="bg-[#12121a] border border-[#1e1e2e] rounded-xl p-4 mb-4">
            <div className="flex items-center justify-between mb-1.5">
              <span className="text-xs text-gray-400">Remediation Progress</span>
              <span className="text-xs font-mono" style={{ color: barColor }}>{resolved.length}/{actionable.length} resolved ({pct}%)</span>
            </div>
            <div className="h-2 bg-[#0a0a0f] rounded-full overflow-hidden">
              <div className="h-full rounded-full transition-all duration-500" style={{ width: `${pct}%`, backgroundColor: barColor }} />
            </div>
          </div>
        ) : null
      })()}

      {/* Filters + CSV export */}
      <div className="flex gap-3 mb-4">
        <select value={sevFilter} onChange={e => setSevFilter(e.target.value)}
          className="bg-[#12121a] border border-[#1e1e2e] rounded-lg px-3 py-1.5 text-xs text-gray-300 focus:outline-none focus:border-[#00ff88]/50">
          <option value="all">All severities</option>
          {severityOrder.map(s => <option key={s} value={s}>{s}</option>)}
        </select>
        <select value={modFilter} onChange={e => setModFilter(e.target.value)}
          className="bg-[#12121a] border border-[#1e1e2e] rounded-lg px-3 py-1.5 text-xs text-gray-300 focus:outline-none focus:border-[#00ff88]/50">
          <option value="all">All modules</option>
          {uniqueModules.map(m => <option key={m} value={m}>{m}</option>)}
        </select>
        <select value={statusFilter} onChange={e => setStatusFilter(e.target.value)}
          className="bg-[#12121a] border border-[#1e1e2e] rounded-lg px-3 py-1.5 text-xs text-gray-300 focus:outline-none focus:border-[#00ff88]/50">
          <option value="all">All statuses</option>
          <option value="active">Active</option>
          <option value="resolved">Resolved</option>
          <option value="dismissed">Dismissed</option>
          <option value="false_positive">False positive</option>
          <option value="monitoring">Monitoring</option>
        </select>
        <button
          onClick={() => {
            const rows = [['Severity','Module','Title','Category','Status','Confidence','Indicator','Date','Description'].join(',')]
            filteredFindings.forEach(f => {
              const esc = (v) => `"${String(v || '').replace(/"/g, '""')}"`
              rows.push([
                esc(f.severity), esc(f.module), esc(f.title), esc(f.category),
                esc(f.status), f.confidence != null ? Math.round(f.confidence * 100) + '%' : '',
                esc(f.indicator_value), f.first_seen ? new Date(f.first_seen).toISOString() : '',
                esc(f.description),
              ].join(','))
            })
            const blob = new Blob([rows.join('\n')], { type: 'text/csv' })
            const url = URL.createObjectURL(blob)
            const a = document.createElement('a')
            a.href = url
            a.download = `xpose-findings-${target.email}-${new Date().toISOString().slice(0,10)}.csv`
            a.click()
            URL.revokeObjectURL(url)
          }}
          className="ml-auto text-xs text-gray-400 hover:text-[#00ff88] border border-[#1e1e2e] rounded-lg px-3 py-1.5 hover:border-[#00ff88]/30 transition-colors"
        >
          Export CSV
        </button>
      </div>

      <div className="bg-[#12121a] border border-[#1e1e2e] rounded-xl overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-xs text-gray-500 uppercase tracking-wider border-b border-[#1e1e2e]">
              <th className="w-8"></th>
              <th className="text-left px-4 py-3">Severity</th>
              <th className="text-left px-4 py-3">Module</th>
              <th className="text-left px-4 py-3">Title</th>
              <th className="text-left px-4 py-3">Category</th>
              <th className="text-left px-4 py-3">Confidence</th>
              <th className="text-left px-4 py-3">Status</th>
              <th className="text-left px-4 py-3">Date</th>
            </tr>
          </thead>
          <tbody>
            {filteredFindings.slice(0, findingsLimit).map((f, i) => (
              <Fragment key={f.id}>
                <tr
                  onClick={() => setExpanded(expanded === f.id ? null : f.id)}
                  className={`border-t border-[#1e1e2e] cursor-pointer hover:bg-white/[0.03] ${i % 2 === 1 ? 'bg-white/[0.02]' : ''}`}>
                  <td className="px-2 text-gray-500">
                    {expanded === f.id ? <ChevronDown className="w-3 h-3" /> : <ChevronRight className="w-3 h-3" />}
                  </td>
                  <td className="px-4 py-3">
                    <span className="inline-block text-xs font-medium px-2 py-0.5 rounded-full"
                      style={{ backgroundColor: (severityColors[f.severity] || '#666688') + '26', color: severityColors[f.severity] || '#666688' }}>
                      {f.severity}
                    </span>
                  </td>
                  <td className="px-4 py-3 font-mono text-xs text-gray-400">{f.module}</td>
                  <td className="px-4 py-3">{f.title}</td>
                  <td className="px-4 py-3 text-gray-400 text-xs">{f.category}</td>
                  <td className="px-4 py-3">
                    {f.confidence != null && (
                      <span className="inline-block text-[10px] font-mono px-1.5 py-0.5 rounded"
                        style={{
                          backgroundColor: (f.confidence >= 0.8 ? '#00ff88' : f.confidence >= 0.6 ? '#ffcc00' : '#ff8800') + '20',
                          color: f.confidence >= 0.8 ? '#00ff88' : f.confidence >= 0.6 ? '#ffcc00' : '#ff8800',
                        }}>
                        {Math.round(f.confidence * 100)}%
                      </span>
                    )}
                  </td>
                  <td className="px-4 py-3">
                    <span className={`text-xs ${f.status === 'resolved' ? 'text-[#00ff88]' : f.status === 'false_positive' ? 'text-gray-500' : 'text-gray-400'}`}>
                      {f.status}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-gray-400 text-xs">{f.first_seen ? new Date(f.first_seen).toLocaleDateString() : '-'}</td>
                </tr>
                {expanded === f.id && (
                  <tr className="bg-[#0a0a0f]">
                    <td colSpan={8} className="px-6 py-4">
                      <div className="space-y-3">
                        <p className="text-sm text-gray-300">{f.description}</p>
                        <div className="flex items-center gap-4 text-xs text-gray-400">
                          {f.indicator_value && <span><span className="text-gray-500">Indicator:</span> <span className="font-mono">{f.indicator_value}</span></span>}
                          {f.url && <a href={f.url} target="_blank" rel="noreferrer" className="text-[#3388ff] hover:underline inline-flex items-center gap-1">
                            Open link <ExternalLink className="w-3 h-3" />
                          </a>}
                        </div>
                        {/* Enriched data cards per scanner */}
                        {f.data && <FindingDataCard finding={f} />}
                        {f.data && (
                          <details className="text-xs">
                            <summary className="text-gray-500 cursor-pointer hover:text-gray-300">Raw data</summary>
                            <pre className="font-mono text-gray-400 bg-[#12121a] rounded-lg p-3 overflow-x-auto max-h-60 mt-2">
                              {JSON.stringify(f.data, null, 2)}
                            </pre>
                          </details>
                        )}
                        <div className="flex items-center gap-2">
                          <span className="text-[10px] text-gray-500">Status:</span>
                          <select
                            value={f.status || 'active'}
                            onClick={e => e.stopPropagation()}
                            onChange={async (e) => {
                              e.stopPropagation()
                              try {
                                await patchFinding(f.id, { status: e.target.value })
                                load()
                              } catch (err) { alert(err.message) }
                            }}
                            className="bg-[#0a0a0f] border border-[#1e1e2e] rounded px-2 py-1 text-xs focus:outline-none focus:border-[#00ff88]/50"
                          >
                            <option value="active">Active</option>
                            <option value="resolved">Resolved</option>
                            <option value="dismissed">Dismissed</option>
                            <option value="false_positive">False positive</option>
                            <option value="monitoring">Monitoring</option>
                          </select>
                        </div>
                      </div>
                    </td>
                  </tr>
                )}
              </Fragment>
            ))}
            {filteredFindings.length === 0 && (
              <tr><td colSpan={8} className="px-5 py-8 text-center text-gray-500">
                {findings.length === 0 ? 'No findings yet. Launch a scan to discover exposure.' : 'No findings match the current filters.'}
              </td></tr>
            )}
          </tbody>
        </table>
      </div>
      {filteredFindings.length > findingsLimit && (
        <button onClick={() => setFindingsLimit(prev => prev + 20)}
          className="w-full mt-3 py-2.5 text-sm text-gray-400 hover:text-[#00ff88] bg-[#12121a] border border-[#1e1e2e] rounded-lg hover:border-[#00ff88]/30 transition-colors">
          Show more ({filteredFindings.length - findingsLimit} remaining)
        </button>
      )}
    </div>
  )
}
