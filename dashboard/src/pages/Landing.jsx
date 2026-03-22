import { useState, useRef, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../lib/auth'
import { Shield, Radar, Lock, Globe, Zap, Eye, Database, Network, Users, ChevronRight, ArrowRight, Check } from 'lucide-react'
import HeroGraph from '../components/HeroGraph'
import CountUp from '../components/CountUp'
import GenerativeAvatar from '../components/GenerativeAvatar'

const DEMO_AVATARS = [
    { email_hash: 12345, score: 5 },
    { email_hash: 67890, score: 15 },
    { email_hash: 11111, score: 25 },
    { email_hash: 22222, score: 35 },
    { email_hash: 33333, score: 45 },
    { email_hash: 44444, score: 55 },
    { email_hash: 55555, score: 65 },
    { email_hash: 66666, score: 75 },
    { email_hash: 77777, score: 85 },
    { email_hash: 88888, score: 95 },
    { email_hash: 99999, score: 10 },
    { email_hash: 10101, score: 30 },
    { email_hash: 20202, score: 50 },
    { email_hash: 30303, score: 70 },
    { email_hash: 40404, score: 90 },
    { email_hash: 50505, score: 20 },
]

const DEFAULT_SEED_PROPS = { hue: 140, num_points: 6, rotation: 45, saturation: 70, lightness: 50, inner_radius: 0.5, complexity: 3 }

const scoreColor = (score) => {
  if (score >= 80) return '#ff2244'
  if (score >= 60) return '#ff8800'
  if (score >= 40) return '#ffcc00'
  if (score >= 20) return '#3388ff'
  return '#00ff88'
}

const sevColor = (sev) => {
  if (sev === 'critical') return { bg: 'bg-[#ff2244]/20', text: 'text-[#ff2244]' }
  if (sev === 'high') return { bg: 'bg-[#ff8800]/20', text: 'text-[#ff8800]' }
  if (sev === 'medium') return { bg: 'bg-[#ffcc00]/20', text: 'text-[#ffcc00]' }
  return { bg: 'bg-[#3388ff]/20', text: 'text-[#3388ff]' }
}

const FEATURES = [
  { icon: Radar, title: 'Deep OSINT Scanning', desc: '25+ intelligence modules scan breaches, social networks, code repos, DNS, and public databases in 30 seconds.' },
  { icon: Network, title: 'Identity Graph', desc: 'Force-directed graph maps every connection between your accounts, usernames, and exposed data points.' },
  { icon: Eye, title: 'Digital Fingerprint', desc: '8-axis radar chart quantifies your exposure. Eigenvalue topology creates a unique identity signature.' },
  { icon: Database, title: 'Breach Intelligence', desc: 'Cross-references HIBP, XposedOrNot, and paste sites. Shows exactly which credentials leaked and when.' },
  { icon: Users, title: 'Identity Avatars', desc: 'Every email gets a unique 32x32 pixel face. 5.4 billion combinations. The avatar evolves with exposure — calm green at low risk, alarmed red with glitch at high threat.' },
  { icon: Lock, title: 'Actionable Remediation', desc: 'Every finding includes step-by-step remediation. Track progress as you reduce your attack surface.' },
]

const PLANS = [
  {
    name: 'Free', price: '€0', period: '/forever', accent: '#666688',
    features: ['1 target', '5 scans/month', 'Layer 1 scanners', 'Basic exposure score', 'Identity graph'],
    cta: 'Start free', href: '/setup',
  },
  {
    name: 'Consultant', price: '€49', period: '/month', accent: '#00ff88', popular: true,
    features: ['25 targets', '100 scans/month', 'Layer 1 + Layer 2', 'Persona clustering', 'Multi-workspace', 'PDF reports', 'CSV export'],
    cta: 'Start trial', href: '/setup?plan=consultant',
  },
  {
    name: 'Enterprise', price: '€199', period: '/month', accent: '#3388ff',
    features: ['Unlimited targets', 'Unlimited scans', 'All layers', 'Intelligence pipeline', 'API access', 'Priority support', 'Custom modules'],
    cta: 'Contact sales', href: '/setup?plan=enterprise',
  },
]

const STEPS = [
  { num: '01', title: 'Enter an email', desc: 'Any email address — yours, a client\'s, or a test target. No account needed for a quick scan.' },
  { num: '02', title: 'We scan everything', desc: '25+ modules query breaches, social networks, DNS, metadata, archives, and public databases in parallel.' },
  { num: '03', title: 'See your exposure', desc: 'Identity graph, exposure score, persona clusters, and step-by-step remediation — all in one dashboard.' },
]

export default function Landing() {
  const [email, setEmail] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [quickResult, setQuickResult] = useState(null)
  const { token } = useAuth()
  const navigate = useNavigate()
  const pollRef = useRef(null)

  useEffect(() => {
    return () => { if (pollRef.current) clearInterval(pollRef.current) }
  }, [])

  async function handleQuickScan(e) {
    e.preventDefault()
    if (!email || !email.includes('@')) {
      setError('Enter a valid email address')
      return
    }
    setError('')
    setLoading(true)
    setQuickResult(null)

    if (token) {
      navigate(`/targets?scan=${encodeURIComponent(email)}`)
      return
    }

    try {
      const resp = await fetch('/api/v1/scan/quick', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email }),
      })

      if (resp.status === 429) {
        setError('Rate limit reached. Create a free account for unlimited scans.')
        setLoading(false)
        return
      }

      if (!resp.ok) {
        const data = await resp.json().catch(() => ({}))
        setError(data.detail || 'Scan failed. Try again.')
        setLoading(false)
        return
      }

      const data = await resp.json()

      if (data.status === 'completed') {
        setQuickResult(data)
        setLoading(false)
        return
      }

      // Poll for results
      const scanId = data.scan_id
      let attempts = 0
      pollRef.current = setInterval(async () => {
        attempts++
        try {
          const statusResp = await fetch(`/api/v1/scan/quick/${scanId}/status`)
          const statusData = await statusResp.json()
          if (statusData.status === 'completed') {
            clearInterval(pollRef.current)
            pollRef.current = null
            setQuickResult(statusData)
            setLoading(false)
          } else if (attempts >= 40) {
            clearInterval(pollRef.current)
            pollRef.current = null
            setError('Scan taking longer than expected. Create an account to see results.')
            setLoading(false)
          }
        } catch {
          clearInterval(pollRef.current)
          pollRef.current = null
          setError('Connection error')
          setLoading(false)
        }
      }, 1000)

    } catch {
      setError('Network error. Try again.')
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-[#0a0a0f] text-white overflow-x-hidden">
      <style>{`
        @keyframes float {
          0%, 100% { transform: translateY(0px); }
          50% { transform: translateY(-6px); }
        }
        @keyframes fadeInUp {
          from { opacity: 0; transform: translateY(20px); }
          to { opacity: 1; transform: translateY(0); }
        }
      `}</style>

      {/* Nav */}
      <nav className="fixed top-0 w-full z-50 border-b border-[#1e1e2e]/50 bg-[#0a0a0f]/80 backdrop-blur-xl px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Shield className="w-6 h-6 text-[#00ff88]" />
          <span className="text-xl font-bold tracking-tight font-['Instrument_Sans',sans-serif]">xpose</span>
        </div>
        <div className="flex items-center gap-3">
          <a href="/login" className="text-sm text-gray-400 hover:text-white px-3 py-1.5 transition-colors">Sign in</a>
          <a href="/setup" className="text-sm bg-[#00ff88] text-black font-semibold rounded-lg px-4 py-1.5 hover:bg-[#00ff88]/90 transition-colors">
            Create account
          </a>
        </div>
      </nav>

      {/* ═══════════════════ Section 1: Hero ═══════════════════ */}
      <section className="min-h-screen flex items-center justify-center relative pt-16">
        {/* Background grid */}
        <div className="absolute inset-0 opacity-[0.03]" style={{
          backgroundImage: 'linear-gradient(#00ff88 1px, transparent 1px), linear-gradient(90deg, #00ff88 1px, transparent 1px)',
          backgroundSize: '60px 60px',
        }} />

        <div className="max-w-7xl mx-auto px-6 grid lg:grid-cols-2 gap-12 items-center relative z-10">
          {/* Left — Copy + form */}
          <div>
            <div className="inline-flex items-center gap-2 text-xs font-mono text-[#00ff88] bg-[#00ff88]/10 border border-[#00ff88]/20 rounded-full px-3 py-1 mb-6">
              <span className="w-1.5 h-1.5 bg-[#00ff88] rounded-full animate-pulse" />
              v0.28.0 — 76+ intelligence modules
            </div>

            <h1 className="text-4xl md:text-5xl lg:text-6xl font-bold tracking-tight leading-tight mb-4 font-['Instrument_Sans',sans-serif]">
              What does the internet know about{' '}
              <span className="text-[#00ff88]">you</span>?
            </h1>

            <p className="text-lg text-gray-400 mb-8 max-w-lg leading-relaxed">
              Identity Threat Intelligence platform. 25 scanners, 71 scrapers,
              graph-based intelligence engine. See your complete digital exposure in 30 seconds.
            </p>

            {/* Scan form */}
            <form onSubmit={handleQuickScan} className="flex gap-3 max-w-md mb-3">
              <input
                type="email"
                value={email}
                onChange={e => setEmail(e.target.value)}
                placeholder="you@email.com"
                className="flex-1 bg-[#12121a] border border-[#1e1e2e] rounded-lg px-4 py-3.5 text-sm focus:outline-none focus:border-[#00ff88]/50 font-mono placeholder-gray-600 transition-colors"
              />
              <button
                type="submit"
                disabled={loading}
                className="bg-[#00ff88] text-black font-semibold rounded-lg px-6 py-3.5 text-sm hover:bg-[#00ff88]/90 disabled:opacity-50 flex items-center gap-2 transition-all group"
              >
                {loading ? (
                  <Radar className="w-4 h-4 animate-spin" />
                ) : (
                  <>
                    <Radar className="w-4 h-4" /> Scan
                    <ArrowRight className="w-3.5 h-3.5 group-hover:translate-x-0.5 transition-transform" />
                  </>
                )}
              </button>
            </form>
            {error && <p className="text-xs text-[#ff2244] mb-2">{error}</p>}
            <p className="text-xs text-gray-600 font-mono">
              No account required for quick scan · GDPR compliant
            </p>

            {/* Loading animation */}
            {loading && !quickResult && (
              <div className="mt-6 text-center">
                <Radar className="w-8 h-8 text-[#00ff88] animate-spin mx-auto mb-3" />
                <p className="text-sm text-gray-400">Scanning 5 modules...</p>
                <p className="text-xs text-gray-600 mt-1">Results in ~20 seconds</p>
              </div>
            )}

            {/* Quick Result Teaser */}
            {quickResult && (
              <div className="bg-[#12121a] border border-[#1e1e2e] rounded-xl p-6 max-w-lg mt-6" style={{ animation: 'fadeInUp 0.5s ease-out' }}>
                <div className="flex items-center gap-4 mb-4">
                  {quickResult.teaser.avatar_seed ? (
                    <GenerativeAvatar seed={quickResult.teaser.avatar_seed} size={64} score={quickResult.teaser.exposure_score} />
                  ) : (
                    <div className="w-16 h-16 rounded-lg bg-[#1e1e2e] flex items-center justify-center text-2xl font-bold text-gray-500">
                      {(quickResult.email || '?')[0].toUpperCase()}
                    </div>
                  )}
                  <div>
                    <h3 className="text-lg font-semibold">
                      {quickResult.teaser.display_name || quickResult.email}
                    </h3>
                    <div className="flex gap-3 text-sm mt-1">
                      <span style={{ color: scoreColor(quickResult.teaser.exposure_score) }}>
                        Exposure: {quickResult.teaser.exposure_score}
                      </span>
                      <span style={{ color: scoreColor(quickResult.teaser.threat_score) }}>
                        Threat: {quickResult.teaser.threat_score}
                      </span>
                    </div>
                  </div>
                </div>

                <div className="grid grid-cols-3 gap-3 mb-4">
                  <div className="bg-[#0a0a0f] rounded-lg p-3 text-center">
                    <div className="text-xl font-mono font-bold text-[#00ff88]">{quickResult.teaser.accounts_count}</div>
                    <div className="text-[10px] text-gray-500">Accounts</div>
                  </div>
                  <div className="bg-[#0a0a0f] rounded-lg p-3 text-center">
                    <div className="text-xl font-mono font-bold text-[#ffcc00]">{quickResult.teaser.sources_count}</div>
                    <div className="text-[10px] text-gray-500">Sources</div>
                  </div>
                  <div className="bg-[#0a0a0f] rounded-lg p-3 text-center">
                    <div className="text-xl font-mono font-bold">{quickResult.teaser.fingerprint_risk}</div>
                    <div className="text-[10px] text-gray-500">Risk Level</div>
                  </div>
                </div>

                {/* Top findings visible */}
                <div className="space-y-2 mb-3">
                  {(quickResult.teaser.top_findings || []).slice(0, 3).map((f, i) => {
                    const c = sevColor(f.severity)
                    return (
                      <div key={i} className="flex items-center gap-2 text-sm">
                        <span className={`text-[10px] px-1.5 py-0.5 rounded-full ${c.bg} ${c.text}`}>{f.severity}</span>
                        <span className="text-gray-300 truncate">{f.title}</span>
                      </div>
                    )
                  })}
                </div>

                {/* Blurred findings (upsell) */}
                <div className="relative">
                  <div className="space-y-2 blur-sm select-none">
                    {[1,2,3,4,5].map(i => (
                      <div key={i} className="flex items-center gap-2 text-sm">
                        <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-gray-800 text-gray-600">medium</span>
                        <span className="text-gray-600">Finding detail hidden — create account to view</span>
                      </div>
                    ))}
                  </div>
                  <div className="absolute inset-0 flex items-center justify-center">
                    <a href={quickResult.upsell?.cta_url || `/setup?email=${encodeURIComponent(email)}`}
                       className="bg-[#00ff88] text-black font-bold rounded-lg px-6 py-3 text-sm hover:bg-[#00ff88]/90 transition-all hover:scale-105 shadow-lg shadow-[#00ff88]/20">
                      See full report — Free
                    </a>
                  </div>
                </div>

                <p className="text-center text-xs text-gray-600 mt-4">
                  Full scan includes 71 scrapers, persona clustering, identity estimation, and remediation plan.
                </p>
              </div>
            )}
          </div>

          {/* Right — Pixel Avatar Grid */}
          <div className="flex flex-col items-center lg:items-end">
            <div className="grid grid-cols-4 gap-3 mb-8 mx-auto max-w-[300px]">
              {DEMO_AVATARS.map((demo, i) => (
                <div key={i} className="relative group" style={{
                  animation: `float ${3 + (i % 4) * 0.5}s ease-in-out infinite`,
                  animationDelay: `${i * 0.2}s`,
                }}>
                  <GenerativeAvatar
                    seed={{ email_hash: demo.email_hash, ...DEFAULT_SEED_PROPS }}
                    size={64}
                    score={demo.score}
                    className="rounded-lg border border-[#1e1e2e] hover:border-[#00ff88]/50 transition-colors cursor-pointer"
                  />
                  <div className="absolute -bottom-1 -right-1 text-[8px] font-mono px-1 rounded opacity-0 group-hover:opacity-100 transition-opacity"
                    style={{ backgroundColor: scoreColor(demo.score), color: '#000' }}>
                    {demo.score}
                  </div>
                </div>
              ))}
            </div>
            <p className="text-xs text-gray-500 mb-8 max-w-md mx-auto text-center">
              Every identity gets a unique pixel avatar generated from their digital fingerprint.
              Green = low exposure. Red = high threat. The face evolves as your digital footprint changes.
            </p>
          </div>
        </div>

        {/* Scroll indicator */}
        <div className="absolute bottom-8 left-1/2 -translate-x-1/2 flex flex-col items-center gap-2 text-gray-600">
          <span className="text-xs font-mono">scroll</span>
          <div className="w-px h-8 bg-gradient-to-b from-gray-600 to-transparent" />
        </div>
      </section>

      {/* ═══════════════════ Section 2: How it works ═══════════════════ */}
      <section className="min-h-screen flex items-center justify-center py-24 relative">
        <div className="max-w-5xl mx-auto px-6">
          <div className="text-center mb-16">
            <span className="text-xs font-mono text-[#00ff88] tracking-widest uppercase">How it works</span>
            <h2 className="text-3xl md:text-4xl font-bold mt-3 font-['Instrument_Sans',sans-serif]">
              Three steps to full visibility
            </h2>
          </div>

          <div className="grid md:grid-cols-3 gap-8">
            {STEPS.map((step, i) => (
              <div key={step.num} className="relative group">
                {/* Connector line */}
                {i < 2 && (
                  <div className="hidden md:block absolute top-8 left-[60%] w-[80%] h-px bg-gradient-to-r from-[#1e1e2e] to-[#1e1e2e]/0" />
                )}
                <div className="bg-[#12121a] border border-[#1e1e2e] rounded-xl p-6 hover:border-[#00ff88]/20 transition-all duration-300 group-hover:shadow-[0_0_30px_rgba(0,255,136,0.05)]">
                  <span className="text-4xl font-bold font-mono text-[#00ff88]/20 group-hover:text-[#00ff88]/40 transition-colors">{step.num}</span>
                  <h3 className="text-lg font-semibold mt-2 mb-2">{step.title}</h3>
                  <p className="text-sm text-gray-400 leading-relaxed">{step.desc}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ═══════════════════ Section 3: Features Grid ═══════════════════ */}
      <section className="min-h-screen flex items-center justify-center py-24 relative">
        <div className="max-w-6xl mx-auto px-6">
          <div className="text-center mb-16">
            <span className="text-xs font-mono text-[#00ff88] tracking-widest uppercase">Capabilities</span>
            <h2 className="text-3xl md:text-4xl font-bold mt-3 font-['Instrument_Sans',sans-serif]">
              Intelligence-grade OSINT
            </h2>
            <p className="text-gray-400 mt-3 max-w-lg mx-auto">
              Professional tools with consumer-grade UX. Every finding is an Identity IOC.
            </p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {FEATURES.map(({ icon: Icon, title, desc }) => (
              <div key={title} className="bg-[#12121a] border border-[#1e1e2e] rounded-xl p-6 hover:border-[#00ff88]/20 transition-all duration-300 group hover:shadow-[0_0_30px_rgba(0,255,136,0.05)]">
                <div className="w-10 h-10 rounded-lg bg-[#00ff88]/10 flex items-center justify-center mb-4 group-hover:bg-[#00ff88]/15 transition-colors">
                  <Icon className="w-5 h-5 text-[#00ff88]" />
                </div>
                <h3 className="text-sm font-semibold mb-2">{title}</h3>
                <p className="text-xs text-gray-400 leading-relaxed">{desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ═══════════════════ Section 4: Stats Counter ═══════════════════ */}
      <section className="py-24 relative">
        <div className="max-w-5xl mx-auto px-6">
          <div className="bg-[#12121a] border border-[#1e1e2e] rounded-2xl p-12 relative overflow-hidden">
            {/* Background accent */}
            <div className="absolute top-0 left-1/2 -translate-x-1/2 w-96 h-px bg-gradient-to-r from-transparent via-[#00ff88]/30 to-transparent" />

            <div className="grid grid-cols-2 md:grid-cols-4 gap-8 text-center">
              <div>
                <div className="text-3xl md:text-4xl font-mono font-bold text-[#00ff88]">
                  <CountUp target={71} />
                </div>
                <div className="text-xs text-gray-400 mt-2 font-mono">Scrapers</div>
              </div>
              <div>
                <div className="text-3xl md:text-4xl font-mono font-bold text-[#00ff88]">
                  <CountUp target={25} />
                </div>
                <div className="text-xs text-gray-400 mt-2 font-mono">Scanners</div>
              </div>
              <div>
                <div className="text-3xl md:text-4xl font-mono font-bold text-[#00ff88]">
                  <CountUp target={5} suffix="B+" />
                </div>
                <div className="text-xs text-gray-400 mt-2 font-mono">Unique Avatars</div>
              </div>
              <div>
                <div className="text-3xl md:text-4xl font-mono font-bold text-[#00ff88]">
                  <CountUp target={3} />
                </div>
                <div className="text-xs text-gray-400 mt-2 font-mono">Plans</div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ═══════════════════ Section 5: Pricing ═══════════════════ */}
      <section className="min-h-screen flex items-center justify-center py-24 relative">
        <div className="max-w-5xl mx-auto px-6">
          <div className="text-center mb-16">
            <span className="text-xs font-mono text-[#00ff88] tracking-widest uppercase">Pricing</span>
            <h2 className="text-3xl md:text-4xl font-bold mt-3 font-['Instrument_Sans',sans-serif]">
              Simple, transparent pricing
            </h2>
          </div>

          <div className="grid md:grid-cols-3 gap-6">
            {PLANS.map(plan => (
              <div key={plan.name}
                className={`bg-[#12121a] border rounded-xl p-6 relative transition-all duration-300 hover:shadow-[0_0_30px_rgba(0,255,136,0.05)] ${
                  plan.popular ? 'border-[#00ff88]/40 shadow-[0_0_40px_rgba(0,255,136,0.08)]' : 'border-[#1e1e2e] hover:border-[#1e1e2e]'
                }`}
              >
                {plan.popular && (
                  <div className="absolute -top-3 left-1/2 -translate-x-1/2 text-[10px] font-mono font-semibold bg-[#00ff88] text-black px-3 py-1 rounded-full">
                    MOST POPULAR
                  </div>
                )}
                <div className="mb-6">
                  <h3 className="text-lg font-semibold" style={{ color: plan.accent }}>{plan.name}</h3>
                  <div className="flex items-baseline gap-1 mt-2">
                    <span className="text-3xl font-bold font-mono">{plan.price}</span>
                    <span className="text-sm text-gray-500">{plan.period}</span>
                  </div>
                </div>
                <ul className="space-y-3 mb-8">
                  {plan.features.map(f => (
                    <li key={f} className="flex items-center gap-2 text-sm text-gray-300">
                      <Check className="w-3.5 h-3.5 shrink-0" style={{ color: plan.accent }} />
                      {f}
                    </li>
                  ))}
                </ul>
                <a href={plan.href}
                  className={`block text-center text-sm font-semibold rounded-lg py-2.5 transition-all ${
                    plan.popular
                      ? 'bg-[#00ff88] text-black hover:bg-[#00ff88]/90'
                      : 'border border-[#1e1e2e] text-gray-300 hover:border-gray-500'
                  }`}
                >
                  {plan.cta}
                </a>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ═══════════════════ Section 6: Footer ═══════════════════ */}
      <footer className="border-t border-[#1e1e2e] py-12">
        <div className="max-w-5xl mx-auto px-6">
          <div className="flex flex-col md:flex-row items-center justify-between gap-4">
            <div className="flex items-center gap-2">
              <Shield className="w-5 h-5 text-[#00ff88]" />
              <span className="font-bold font-['Instrument_Sans',sans-serif]">xpose</span>
              <span className="text-xs text-gray-600 font-mono ml-2">v0.28.0</span>
            </div>
            <p className="text-xs text-gray-600 font-mono text-center">
              Identity Threat Intelligence · Open Source · GDPR Compliant
            </p>
            <div className="flex items-center gap-4 text-xs text-gray-500">
              <a href="https://github.com/nabz0r/xposeTIP" className="hover:text-white transition-colors">GitHub</a>
              <a href="/login" className="hover:text-white transition-colors">Sign in</a>
            </div>
          </div>
        </div>
      </footer>
    </div>
  )
}
