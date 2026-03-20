import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../lib/auth'
import { Shield, Radar, Lock, Globe, Zap, ChevronRight } from 'lucide-react'
import FingerprintRadar from '../components/FingerprintRadar'

const STATS = [
  { value: '25+', label: 'Scanners', desc: 'Intelligence modules' },
  { value: '120+', label: 'Sites', desc: 'Account enumeration' },
  { value: 'Free', label: 'Core', desc: 'Open source engine' },
  { value: 'GDPR', label: 'Compliant', desc: 'EU privacy ready' },
]

export default function Landing() {
  const [email, setEmail] = useState('')
  const [loading, setLoading] = useState(false)
  const [quickResult, setQuickResult] = useState(null)
  const [error, setError] = useState('')
  const { token } = useAuth()
  const navigate = useNavigate()

  async function handleQuickScan(e) {
    e.preventDefault()
    if (!email || !email.includes('@')) {
      setError('Enter a valid email address')
      return
    }
    setError('')
    setLoading(true)

    // If logged in, create target + scan
    if (token) {
      navigate(`/targets?scan=${encodeURIComponent(email)}`)
      return
    }

    // Quick scan (no auth)
    try {
      const resp = await fetch('/api/v1/scan/quick', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email }),
      })
      if (!resp.ok) {
        const data = await resp.json().catch(() => ({}))
        setError(data.detail || 'Scan failed. Try again.')
        setLoading(false)
        return
      }
      const data = await resp.json()
      setQuickResult(data)
    } catch {
      setError('Network error. Try again.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-[#0a0a0f] text-white flex flex-col">
      {/* Nav */}
      <nav className="border-b border-[#1e1e2e] px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Shield className="w-6 h-6 text-[#00ff88]" />
          <span className="text-xl font-bold tracking-tight">xpose</span>
        </div>
        <div className="flex items-center gap-3">
          <a href="/login" className="text-sm text-gray-400 hover:text-white px-3 py-1.5">Sign in</a>
          <a href="/setup" className="text-sm bg-[#00ff88] text-black font-semibold rounded-lg px-4 py-1.5 hover:bg-[#00ff88]/90">
            Create account
          </a>
        </div>
      </nav>

      {/* Hero */}
      <div className="flex-1 flex flex-col items-center justify-center px-6 py-20">
        <div className="max-w-2xl mx-auto text-center">
          <div className="inline-flex items-center gap-2 text-[#00ff88] mb-6">
            <Shield className="w-10 h-10" />
            <h1 className="text-4xl md:text-5xl font-bold tracking-tight">xpose</h1>
          </div>
          <p className="text-lg md:text-xl text-gray-300 mb-2">
            Identity Threat Intelligence Platform
          </p>
          <p className="text-2xl md:text-3xl font-semibold mb-8">
            What does the internet know about <span className="text-[#00ff88]">you</span>?
          </p>

          {/* Scan form */}
          <form onSubmit={handleQuickScan} className="flex gap-3 max-w-md mx-auto mb-4">
            <input
              type="email"
              value={email}
              onChange={e => setEmail(e.target.value)}
              placeholder="Enter your email"
              className="flex-1 bg-[#12121a] border border-[#1e1e2e] rounded-lg px-4 py-3 text-sm focus:outline-none focus:border-[#00ff88]/50 font-mono"
            />
            <button
              type="submit"
              disabled={loading}
              className="bg-[#00ff88] text-black font-semibold rounded-lg px-6 py-3 text-sm hover:bg-[#00ff88]/90 disabled:opacity-50 flex items-center gap-2"
            >
              {loading ? (
                <Radar className="w-4 h-4 animate-spin" />
              ) : (
                <>
                  <Radar className="w-4 h-4" /> Scan
                </>
              )}
            </button>
          </form>
          {error && <p className="text-xs text-[#ff2244] mb-4">{error}</p>}
          <p className="text-sm text-gray-500 mb-12">
            In 30 seconds, discover your digital exposure
          </p>

          {/* Quick result preview with fingerprint */}
          {quickResult && (() => {
            // Build lightweight fingerprint from quick scan findings
            const findings = quickResult.findings || []
            const breaches = findings.filter(f => f.category === 'breach').length
            const social = findings.filter(f => f.category === 'social_account' || f.category === 'social').length
            const security = findings.filter(f => (f.title || '').toLowerCase().includes('no spf') || (f.title || '').toLowerCase().includes('no dmarc')).length
            const dataTypes = new Set()
            findings.forEach(f => { if (f.data?.data_classes) f.data.data_classes.forEach(d => dataTypes.add(d)); if (f.data?.DataClasses) f.data.DataClasses.forEach(d => dataTypes.add(d)) })
            const maxA = 15, maxP = 10, maxB = 5, maxD = 8, maxS = 4
            const quickFp = {
              axes: {
                accounts: Math.min(1, social / maxA),
                platforms: Math.min(1, social / maxP),
                username_reuse: 0,
                breaches: Math.min(1, breaches / maxB),
                geo_spread: Math.min(1, findings.filter(f => f.data?.country).length / 5),
                data_leaked: Math.min(1, dataTypes.size / maxD),
                email_age: 0,
                security: Math.min(1, security / maxS),
              },
              color: findings.length > 10 ? '#E24B4A' : findings.length > 5 ? '#D85A30' : findings.length > 2 ? '#EF9F27' : '#1D9E75',
              fill_color: findings.length > 5 ? 'rgba(225,50,50,0.08)' : 'rgba(29,158,117,0.12)',
              hash: '--------',
              score: Math.min(100, Math.round(findings.length * 5)),
              risk_level: findings.length > 10 ? 'HIGH' : findings.length > 5 ? 'MODERATE' : 'LOW',
              scars: [],
              raw_values: { accounts: social, platforms: social, username_reuse: 0, breaches, geo_spread: 0, data_leaked: dataTypes.size, email_age_years: 0, security_weak: security },
            }
            return (
              <div className="bg-[#12121a] border border-[#1e1e2e] rounded-xl p-6 max-w-lg mx-auto mb-8">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-sm font-semibold">Your Digital Fingerprint</h3>
                  <span className="text-xs font-mono text-gray-500">{findings.length} findings</span>
                </div>
                <FingerprintRadar fingerprint={quickFp} size="large" animate={true} />
                <div className="space-y-2 mt-4 text-left">
                  {findings.slice(0, 5).map((f, i) => (
                    <div key={i} className="flex items-center gap-2 text-sm">
                      <span className="inline-block text-[10px] font-medium px-1.5 py-0.5 rounded-full"
                        style={{
                          backgroundColor: (f.severity === 'critical' ? '#ff2244' : f.severity === 'high' ? '#ff8800' : f.severity === 'medium' ? '#ffcc00' : '#3388ff') + '26',
                          color: f.severity === 'critical' ? '#ff2244' : f.severity === 'high' ? '#ff8800' : f.severity === 'medium' ? '#ffcc00' : '#3388ff',
                        }}>
                        {f.severity}
                      </span>
                      <span className="text-gray-300 truncate">{f.title}</span>
                    </div>
                  ))}
                  {findings.length > 5 && (
                    <div className="relative">
                      <div className="space-y-2 blur-sm">
                        {findings.slice(5, 8).map((f, i) => (
                          <div key={i} className="flex items-center gap-2 text-sm">
                            <span className="inline-block text-[10px] px-1.5 py-0.5 rounded-full bg-gray-800 text-gray-500">{f.severity}</span>
                            <span className="text-gray-500 truncate">{f.title}</span>
                          </div>
                        ))}
                      </div>
                      <div className="absolute inset-0 flex items-center justify-center">
                        <a href={`/setup?email=${encodeURIComponent(email)}`}
                           className="bg-[#00ff88] text-black font-semibold rounded-lg px-4 py-2 text-xs hover:bg-[#00ff88]/90">
                          Sign up to see full audit
                        </a>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            )
          })()}

          {/* Stats */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 max-w-lg mx-auto mb-16">
            {STATS.map(s => (
              <div key={s.label} className="bg-[#12121a] border border-[#1e1e2e] rounded-xl p-4 text-center hover:border-[#00ff88]/20 transition-colors">
                <div className="text-2xl font-mono font-bold text-[#00ff88]">{s.value}</div>
                <div className="text-xs text-gray-400 mt-1">{s.label}</div>
              </div>
            ))}
          </div>

          {/* Features */}
          <div className="grid md:grid-cols-3 gap-6 max-w-3xl mx-auto text-left">
            {[
              { icon: Radar, title: 'Deep OSINT', desc: '25+ intelligence scanners check your email across breaches, social networks, code repos, and public databases.' },
              { icon: Lock, title: 'Actionable Security', desc: 'Every finding comes with remediation steps. We tell you exactly how to fix your exposure.' },
              { icon: Zap, title: 'Intelligence Engine', desc: 'Auto cross-references usernames, IPs, domains, and breaches to surface hidden connections.' },
            ].map(({ icon: Icon, title, desc }) => (
              <div key={title} className="bg-[#12121a] border border-[#1e1e2e] rounded-xl p-5 hover:border-[#00ff88]/20 transition-colors">
                <Icon className="w-8 h-8 text-[#00ff88] mb-3" />
                <h3 className="text-sm font-semibold mb-2">{title}</h3>
                <p className="text-xs text-gray-400 leading-relaxed">{desc}</p>
              </div>
            ))}
          </div>

          <p className="text-sm text-gray-600 mt-12">
            Built in Luxembourg. Open source. GDPR compliant.
          </p>
        </div>
      </div>
    </div>
  )
}
