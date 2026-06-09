import { useEffect, useState } from 'react'
import { ShieldCheck, MapPin, Globe, Mail, AlertTriangle, Download } from 'lucide-react'
import FingerprintRadar from '../components/FingerprintRadar'

// S253 — Subject Portal. Public route. The token rides in the URL fragment
// (#t=...) — never in a query param, never in localStorage. We read it on
// mount, purge it from the URL via history.replaceState, then fetch the
// read-only profile through the consent-router gate.
//
// The portal is empowerment, not surveillance: this is what the internet
// already exposes about the subject, woven into one view, returned to them.

export default function Portal() {
  const [state, setState] = useState({ phase: 'loading', profile: null, error: null })

  useEffect(() => {
    // 1. Extract the token from the URL fragment.
    const hash = window.location.hash || ''
    const m = hash.match(/(?:^#|&)t=([0-9a-fA-F]{8,})/)
    const token = m?.[1]
    // 2. Purge the fragment from the URL bar — keep the path, drop the hash.
    if (token) {
      try { window.history.replaceState({}, '', window.location.pathname + window.location.search) } catch {}
    }
    if (!token) {
      setState({ phase: 'missing', profile: null, error: null })
      return
    }
    // 3. Exchange the token for the profile.
    fetch(`/consent/portal/profile?t=${encodeURIComponent(token)}`)
      .then(async (r) => {
        if (r.status === 401) return setState({ phase: 'expired', profile: null, error: null })
        if (r.status === 404) return setState({ phase: 'expired', profile: null, error: null })
        if (!r.ok) {
          const detail = await r.text().catch(() => '')
          return setState({ phase: 'error', profile: null, error: detail || `HTTP ${r.status}` })
        }
        const data = await r.json()
        setState({ phase: 'ready', profile: data, error: null })
      })
      .catch((e) => setState({ phase: 'error', profile: null, error: String(e) }))
  }, [])

  if (state.phase === 'loading') return <PortalShell><Loading /></PortalShell>
  if (state.phase === 'missing' || state.phase === 'expired') {
    return (
      <PortalShell>
        <ExpiredCard
          title={state.phase === 'missing' ? 'No portal token' : 'Link expired'}
          body={
            state.phase === 'missing'
              ? 'This page is only reachable through a one-time link returned to you after you sign in. Ask the operator who scanned you to issue a fresh consent link.'
              : 'The portal link has expired (30 min lifetime). Ask the operator who scanned you to issue a fresh consent link.'
          }
        />
      </PortalShell>
    )
  }
  if (state.phase === 'error') {
    return (
      <PortalShell>
        <ExpiredCard
          title="Portal unavailable"
          body={`We couldn't load your profile right now. ${state.error || ''}`}
        />
      </PortalShell>
    )
  }

  return (
    <PortalShell>
      <ProfileView profile={state.profile} />
    </PortalShell>
  )
}

function PortalShell({ children }) {
  return (
    <div className="min-h-screen bg-[#0a0a0f] text-white">
      <header className="border-b border-[#1e1e2e] px-6 py-5 flex items-center gap-3">
        <ShieldCheck className="w-5 h-5 text-[#00ff88]" />
        <span className="font-bold text-sm tracking-wider">Subject Portal</span>
        <span className="ml-auto text-[10px] font-mono text-gray-600">read-only · returned to you</span>
      </header>
      {children}
      <footer className="border-t border-[#1e1e2e] px-6 py-4 mt-12 text-[10px] font-mono text-gray-600 text-center">
        Your access expires automatically. No account, nothing stored locally — close this tab and the link is gone.
      </footer>
    </div>
  )
}

function Loading() {
  return (
    <div className="max-w-2xl mx-auto px-6 py-16 text-center text-gray-500 text-sm font-mono">
      Loading your portrait…
    </div>
  )
}

function ExpiredCard({ title, body }) {
  return (
    <div className="max-w-lg mx-auto px-6 py-16 text-center">
      <AlertTriangle className="w-8 h-8 text-[#ff8800] mx-auto mb-3" />
      <h1 className="text-xl font-bold mb-3 font-['Instrument_Sans',sans-serif]">{title}</h1>
      <p className="text-sm text-gray-400 leading-relaxed">{body}</p>
    </div>
  )
}

// S255 — RGPD art.20 data-portability export. Serialises the exact DTO
// the subject sees (already scrubbed of operator-only fields by S253) into
// a structured, machine-readable JSON file. No new endpoint, no fresh
// network call — the subject downloads what's already in their view.
function downloadData(profile) {
  const payload = {
    export_metadata: {
      exported_at: new Date().toISOString(),
      source: 'xposeTIP',
      format: 'RGPD art.20 — data portability',
    },
    profile,
  }
  const blob = new Blob([JSON.stringify(payload, null, 2)], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `my-xposetip-data-${new Date().toISOString().slice(0, 10)}.json`
  document.body.appendChild(a)
  a.click()
  a.remove()
  URL.revokeObjectURL(url)
}

function ProfileView({ profile }) {
  const p = profile || {}
  const name = p.primary_name || (p.email || '').split('@')[0]
  const fp = p.fingerprint
  const langs = p.languages?.languages || []
  const tz = p.timezone
  const geo = p.geo_consistency
  const emailStatus = p.email_status
  const breaches = p.breach_summary?.count || 0
  const social = p.social_profiles || []
  return (
    <main className="max-w-4xl mx-auto px-6 py-10">
      <section className="mb-8 text-center">
        <div className="text-xs font-mono uppercase tracking-wider text-[#00ff88]/70 mb-3">
          Identity returned
        </div>
        <h1 className="text-3xl md:text-4xl font-bold mb-3 font-['Instrument_Sans',sans-serif] leading-tight">
          This is what the internet exposes about you.
        </h1>
        <p className="text-sm text-gray-400 max-w-xl mx-auto leading-relaxed">
          Woven into one view, returned to you. You can close this tab any time —
          this is your read-only mirror, not a new account.
        </p>
      </section>

      {/* Header card */}
      <div className="bg-[#12121a] border border-[#1e1e2e] rounded-xl p-5 mb-4 flex flex-col md:flex-row gap-5 items-start">
        <div className="flex-1 min-w-0">
          <h2 className="text-2xl font-bold font-['Instrument_Sans',sans-serif] mb-1">{name}</h2>
          <p className="text-sm font-mono text-gray-400 break-all flex items-center gap-2">
            <Mail className="w-3.5 h-3.5" />{p.email}
          </p>
          {p.location && (
            <p className="text-xs text-gray-500 mt-1 flex items-center gap-1.5">
              <MapPin className="w-3 h-3" />{p.location}{p.company ? ` · ${p.company}` : ''}
            </p>
          )}
          {p.bio && (
            <p className="text-sm text-gray-300 mt-2 italic leading-relaxed">"{p.bio}"</p>
          )}
        </div>
        {p.exposure_score != null && (
          <div className="shrink-0 text-right">
            <div className="text-[10px] uppercase tracking-wider text-gray-500 font-mono">Exposure</div>
            <div className="text-3xl font-mono font-bold text-[#ff8800]">{p.exposure_score}</div>
          </div>
        )}
      </div>

      {/* S255 — Data portability (RGPD art.20). Downloads the same DTO
          already in state — no extra fetch, no operator fields. */}
      <div className="flex items-center gap-3 mb-4 px-1">
        <button
          type="button"
          onClick={() => downloadData(profile)}
          className="inline-flex items-center gap-2 px-3 py-1.5 rounded-md text-[11px] font-mono bg-[#1e1e2e] text-[#00ff88] border border-[#00ff88]/40 hover:bg-[#00ff88]/10 transition-colors"
          title="Save a structured JSON copy of everything shown above. RGPD art.20 — data portability."
        >
          <Download className="w-3.5 h-3.5" />
          Download my data
        </button>
        <p className="text-[11px] text-gray-500">
          Everything we hold about you, in a portable file. It's yours.
        </p>
      </div>

      {/* Two columns: radar + signals */}
      <div className="grid md:grid-cols-[1fr_320px] gap-4">
        <div className="bg-[#12121a] border border-[#1e1e2e] rounded-xl p-6">
          <h3 className="text-xs uppercase tracking-wider text-gray-500 font-mono mb-3">
            Behavioral fingerprint
          </h3>
          {fp ? (
            <div className="flex justify-center">
              <FingerprintRadar fingerprint={fp} size="large" animate />
            </div>
          ) : (
            <p className="text-sm text-gray-500 text-center py-12">
              Fingerprint not yet computed.
            </p>
          )}
        </div>
        <div className="bg-[#12121a] border border-[#1e1e2e] rounded-xl p-4">
          <h3 className="text-xs uppercase tracking-wider text-gray-500 font-mono mb-3">
            Signals
          </h3>
          {emailStatus?.status && (
            <Row
              label="Email"
              value={
                emailStatus.status === 'true' ? '✓ Deliverable' :
                emailStatus.status === 'false' ? '✗ Undeliverable' :
                emailStatus.status === 'risky' ? '⚠ Risky' : '○ Unverified'
              }
              accent="#00ff88"
            />
          )}
          {emailStatus?.provider && <Row label="Provider" value={emailStatus.provider} />}
          {breaches > 0 && (
            <Row label="Breaches" value={String(breaches)} accent="#ff5588" />
          )}
          {geo?.primary_country && (
            <Row
              label="Country"
              value={`${geo.primary_country_name || geo.primary_country} · ${Math.round((geo.consistency_score || 0) * 100)}% consistent`}
            />
          )}
          {tz && tz.utc_offset !== undefined && (
            <Row label="Timezone" value={`UTC${tz.utc_offset >= 0 ? '+' : ''}${tz.utc_offset}`} />
          )}
          {langs.length > 0 && (
            <Row
              label="Languages"
              value={langs.slice(0, 3).map((l) => `${(l.code || '').toUpperCase()} ${Math.round((l.confidence || 0) * 100)}%`).join(' · ')}
            />
          )}
          {social.length > 0 && (
            <div className="mt-3 pt-3 border-t border-[#1e1e2e]">
              <div className="text-[10px] uppercase tracking-wider text-gray-500 font-mono mb-2">
                Accounts surfaced ({social.length})
              </div>
              <div className="flex flex-wrap gap-1.5">
                {social.slice(0, 12).map((s, i) => (
                  <span key={i} className="text-[11px] font-mono px-2 py-0.5 bg-[#1e1e2e] rounded text-gray-300">
                    <Globe className="w-3 h-3 inline mr-1 text-[#3388ff]" />
                    {s.platform || 'unknown'}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>

      <section className="mt-10 text-center">
        <p className="text-sm text-gray-400 max-w-xl mx-auto leading-relaxed">
          You proved control of <span className="text-[#00ff88] font-mono">{p.email}</span> by signing in.
          Everything above was already public — we just brought it back to you in one view.
        </p>
      </section>
    </main>
  )
}

function Row({ label, value, accent }) {
  return (
    <div className="flex items-center justify-between py-1.5 border-b border-[#1e1e2e] last:border-0 text-xs">
      <span className="text-gray-500 font-mono">{label}</span>
      <span className="font-mono" style={{ color: accent || '#e5e7eb' }}>{value}</span>
    </div>
  )
}
