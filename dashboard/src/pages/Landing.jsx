import { useState, useRef, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../lib/auth'
import { Shield, Radar, ArrowRight, Check, KeyRound, Users, Globe, AtSign, Fingerprint, Mail, Camera, Share2, Newspaper, ShieldCheck } from 'lucide-react'
import GenerativeAvatar from '../components/GenerativeAvatar'

// ─── Scroll reveal hook ───
function useScrollReveal() {
  const ref = useRef(null)
  const [visible, setVisible] = useState(false)
  useEffect(() => {
    const observer = new IntersectionObserver(
      ([entry]) => { if (entry.isIntersecting) setVisible(true) },
      { threshold: 0.15 }
    )
    if (ref.current) observer.observe(ref.current)
    return () => observer.disconnect()
  }, [])
  return [ref, visible]
}

function Section({ children, className = '' }) {
  const [ref, visible] = useScrollReveal()
  return (
    <section ref={ref} className={`transition-all duration-700 ${
      visible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-8'
    } ${className}`}>
      {children}
    </section>
  )
}

// ─── Live Counter ───
function LiveCounter() {
  const [count, setCount] = useState(4_237_891_442)
  const ref = useRef(null)
  const [started, setStarted] = useState(false)

  useEffect(() => {
    const observer = new IntersectionObserver(
      ([entry]) => { if (entry.isIntersecting) setStarted(true) },
      { threshold: 0.3 }
    )
    if (ref.current) observer.observe(ref.current)
    return () => observer.disconnect()
  }, [])

  useEffect(() => {
    if (!started) return
    const interval = setInterval(() => {
      setCount(c => c + Math.floor(Math.random() * 3) + 12)
    }, 1000)
    return () => clearInterval(interval)
  }, [started])

  return (
    <div ref={ref}>
      <div className="text-6xl md:text-8xl font-mono font-bold text-[#ff2244] tabular-nums">
        {count.toLocaleString()}
      </div>
      <p className="text-lg text-gray-400 mt-4">
        records leaked — and counting.
      </p>
      <p className="text-sm text-gray-600 mt-2">
        +13 every second. While you're reading this.
      </p>
    </div>
  )
}

// ─── Constants ───
const DEMO_AVATARS = [
  { email_hash: 12345, score: 15 },
  { email_hash: 67890, score: 35 },
  { email_hash: 33333, score: 55 },
  { email_hash: 44444, score: 72 },
  { email_hash: 55555, score: 25 },
  { email_hash: 77777, score: 85 },
  { email_hash: 88888, score: 45 },
  { email_hash: 10101, score: 65 },
  { email_hash: 20202, score: 92 },
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

const PHASES = [
  { until: 15, msg: 'Starting scan...' },
  { until: 40, msg: 'Checking breach databases...' },
  { until: 80, msg: 'Scanning social networks...' },
  { until: 120, msg: 'Analyzing DNS & email security...' },
  { until: 180, msg: 'Cross-referencing usernames...' },
  { until: 240, msg: 'Building your identity profile...' },
  { until: 300, msg: 'Finalizing results...' },
]

const EXPOSURES = [
  { icon: Users, title: 'Digital Footprint Discovery', desc: 'Identify accounts across 35+ social platforms, dev tools, gaming sites. Detect username reuse and cross-platform linkage.' },
  { icon: KeyRound, title: 'Breach & Leak Intelligence', desc: 'Check exposure in data breaches, leaked credentials, and paste sites. Timeline of when data was compromised.' },
  { icon: Newspaper, title: 'Public Exposure Intelligence', desc: 'Automated news monitoring across global media. Sanctions & PEP screening via 40+ watchlists. Corporate directorship tracking.' },
  { icon: Fingerprint, title: '9-Axis Behavioral Radar', desc: 'Unique digital fingerprint across 9 dimensions: accounts, platforms, email age, breaches, username reuse, data leaked, geo spread, security posture, and public exposure.' },
  { icon: Share2, title: 'Identity Graph & Personas', desc: 'PageRank-based confidence propagation. Automatic persona clustering. Name resolution with operator override.' },
  { icon: ShieldCheck, title: 'Compliance Ready', desc: 'Sanctions screening (OFAC, EU, UN, Interpol). PEP detection. Corporate officer identification. Built for KYC/AML workflows.' },
]

const AUDIENCES = [
  { label: 'Individual', desc: 'Check your own exposure.', price: 'Free forever.', href: '/setup', cta: 'Start free' },
  { label: 'Security consultant', desc: 'Audit clients at scale.', price: '€49/month.', href: '/setup?plan=consultant', cta: 'Start trial' },
  { label: 'Organization', desc: 'Protect your team.', price: '€199/month.', href: '/setup?plan=enterprise', cta: 'Contact sales' },
]

function hashEmail(email) {
  let hash = 0
  for (let i = 0; i < (email || '').length; i++) {
    hash = ((hash << 5) - hash) + email.charCodeAt(i)
    hash |= 0
  }
  return Math.abs(hash)
}

// ─── Scan Form Component (reused in hero + final CTA) ───
function ScanForm({ email, setEmail, loading, error, onSubmit }) {
  return (
    <div>
      <form onSubmit={onSubmit} className="flex gap-3 max-w-md">
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
              Scan now
              <ArrowRight className="w-3.5 h-3.5 group-hover:translate-x-0.5 transition-transform" />
            </>
          )}
        </button>
      </form>
      {error && <p className="text-xs text-[#ff2244] mt-2">{error}</p>}
    </div>
  )
}

// ─── Main Component ───
export default function Landing() {
  const [email, setEmail] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [quickResult, setQuickResult] = useState(null)
  const [pollCount, setPollCount] = useState(0)
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
    setPollCount(0)

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

      // Poll for results — 300s max
      const scanId = data.scan_id
      let attempts = 0
      pollRef.current = setInterval(async () => {
        attempts++
        setPollCount(attempts)
        try {
          const statusResp = await fetch(`/api/v1/scan/quick/${scanId}/status`)
          const statusData = await statusResp.json()
          if (statusData.status === 'completed') {
            clearInterval(pollRef.current)
            pollRef.current = null
            setQuickResult(statusData)
            setLoading(false)
          } else if (attempts >= 300) {
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

  const phaseMsg = PHASES.find(p => pollCount < p.until)?.msg || 'Finalizing results...'

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

      {/* ─── Nav ─── */}
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

      {/* ═══════════════════ Section 1: Hero — THE HOOK ═══════════════════ */}
      <section className="min-h-screen flex items-center justify-center relative pt-16">
        {/* Background grid */}
        <div className="absolute inset-0 opacity-[0.02]" style={{
          backgroundImage: 'linear-gradient(#00ff88 1px, transparent 1px), linear-gradient(90deg, #00ff88 1px, transparent 1px)',
          backgroundSize: '60px 60px',
        }} />

        <div className="max-w-7xl mx-auto px-6 grid lg:grid-cols-[1fr_auto] gap-16 items-center relative z-10">
          {/* Left — Copy */}
          <div className="max-w-2xl">
            <div className="inline-flex items-center gap-2 text-xs font-mono text-[#00ff88]/70 mb-8">
              <span className="w-1.5 h-1.5 bg-[#00ff88] rounded-full animate-pulse" />
              Free · No account needed
            </div>

            <h1 className="text-5xl md:text-6xl lg:text-7xl font-bold tracking-tight leading-[1.1] mb-6 font-['Instrument_Sans',sans-serif]">
              Identity Threat<br />
              Intelligence<br />
              <span className="text-gray-500">from one email.</span>
            </h1>

            <p className="text-gray-400 text-lg mb-6 max-w-lg leading-relaxed">
              From a single email address, uncover the complete digital identity: online accounts,
              data breaches, corporate roles, media presence, sanctions exposure, and geographic footprint.
            </p>

            <div className="flex flex-wrap gap-3 text-[11px] font-mono text-gray-500 mb-8">
              <span className="bg-[#1e1e2e] px-2.5 py-1 rounded-full">117 OSINT sources</span>
              <span className="bg-[#1e1e2e] px-2.5 py-1 rounded-full">9-axis behavioral radar</span>
              <span className="bg-[#1e1e2e] px-2.5 py-1 rounded-full">Two-pass intelligence pipeline</span>
            </div>

            <div className="mb-8">
              <ScanForm email={email} setEmail={setEmail} loading={loading} error={error} onSubmit={handleQuickScan} />
            </div>

            <p className="text-sm text-gray-600">
              Takes 30 seconds. We'll show you everything an attacker already knows.
            </p>

            {/* Loading with phase messages */}
            {loading && !quickResult && (
              <div className="mt-10">
                <div className="flex items-center gap-3 mb-2">
                  <Radar className="w-5 h-5 text-[#00ff88] animate-spin" />
                  <span className="text-sm text-gray-300">{phaseMsg}</span>
                </div>
                <div className="w-full max-w-md bg-[#1e1e2e] rounded-full h-1 overflow-hidden">
                  <div
                    className="h-full bg-[#00ff88] rounded-full transition-all duration-1000"
                    style={{ width: `${Math.min((pollCount / 300) * 100, 100)}%` }}
                  />
                </div>
              </div>
            )}

            {/* Quick Result Teaser */}
            {quickResult && (
              <div className="bg-[#12121a] border border-[#1e1e2e] rounded-xl p-6 max-w-lg mt-8" style={{ animation: 'fadeInUp 0.5s ease-out' }}>
                <div className="flex items-center gap-4 mb-4">
                  <GenerativeAvatar
                    seed={quickResult.teaser.avatar_seed || { email_hash: hashEmail(quickResult.email) }}
                    size={64}
                    score={quickResult.teaser.exposure_score || 0}
                  />
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
              </div>
            )}
          </div>

          {/* Right — Ambient avatar grid (3x3) */}
          <div className="hidden lg:grid grid-cols-3 gap-2 opacity-40">
            {DEMO_AVATARS.map((demo, i) => (
              <div key={i} style={{
                animation: `float ${3 + (i % 3) * 0.7}s ease-in-out infinite`,
                animationDelay: `${i * 0.3}s`,
              }}>
                <GenerativeAvatar
                  seed={{ email_hash: demo.email_hash, ...DEFAULT_SEED_PROPS }}
                  size={48}
                  score={demo.score}
                />
              </div>
            ))}
          </div>
        </div>

        {/* Scroll indicator */}
        <div className="absolute bottom-8 left-1/2 -translate-x-1/2 flex flex-col items-center gap-2 text-gray-600">
          <span className="text-xs font-mono">scroll</span>
          <div className="w-px h-8 bg-gradient-to-b from-gray-600 to-transparent" />
        </div>
      </section>

      {/* ═══════════════════ Section 2: THE PROBLEM ═══════════════════ */}
      <Section className="py-32">
        <div className="max-w-3xl mx-auto px-6 text-center">
          <LiveCounter />
          <p className="text-lg md:text-xl text-gray-300 leading-relaxed max-w-xl mx-auto mt-8">
            Your email is probably in there. An attacker can find your name, your accounts,
            your habits — in 30 seconds.
          </p>
          <p className="text-lg md:text-xl text-gray-300 leading-relaxed mt-6 max-w-xl mx-auto">
            We know because <span className="text-white font-semibold">we do the same thing</span>.
            <br />
            The difference? We show you how to fix it.
          </p>
        </div>
      </Section>

      {/* ═══════════════════ Section 3: WHAT WE FIND ═══════════════════ */}
      <Section className="py-32">
        <div className="max-w-4xl mx-auto px-6">
          <h2 className="text-3xl md:text-4xl font-bold text-center mb-16 font-['Instrument_Sans',sans-serif]">
            What we uncover
          </h2>

          <div className="grid md:grid-cols-2 gap-8">
            {EXPOSURES.map(({ icon: Icon, title, desc }) => (
              <div key={title} className="flex gap-4">
                <div className="w-10 h-10 rounded-lg bg-[#1e1e2e] flex items-center justify-center shrink-0">
                  <Icon className="w-5 h-5 text-gray-400" />
                </div>
                <div>
                  <h3 className="text-sm font-semibold mb-1">{title}</h3>
                  <p className="text-sm text-gray-500 leading-relaxed">{desc}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </Section>

      {/* ═══════════════════ Section 4: HOW IT WORKS ═══════════════════ */}
      <Section className="py-32">
        <div className="max-w-4xl mx-auto px-6">
          <h2 className="text-3xl md:text-4xl font-bold text-center mb-16 font-['Instrument_Sans',sans-serif]">
            How it works
          </h2>

          <div className="grid md:grid-cols-3 lg:grid-cols-6 gap-6 text-center">
            <div>
              <div className="text-4xl font-mono font-bold text-[#00ff88]/20 mb-3">01</div>
              <h3 className="text-sm font-semibold mb-1">Collect</h3>
              <p className="text-xs text-gray-500">117 scrapers gather raw data</p>
            </div>
            <div>
              <div className="text-4xl font-mono font-bold text-[#3388ff]/20 mb-3">02</div>
              <h3 className="text-sm font-semibold mb-1">Verify</h3>
              <p className="text-xs text-gray-500">Cross-reference findings</p>
            </div>
            <div>
              <div className="text-4xl font-mono font-bold text-[#ffcc00]/20 mb-3">03</div>
              <h3 className="text-sm font-semibold mb-1">Analyze</h3>
              <p className="text-xs text-gray-500">PageRank graph, confidence propagation</p>
            </div>
            <div>
              <div className="text-4xl font-mono font-bold text-[#ff8800]/20 mb-3">04</div>
              <h3 className="text-sm font-semibold mb-1">Profile</h3>
              <p className="text-xs text-gray-500">Name resolution, personas, locations</p>
            </div>
            <div>
              <div className="text-4xl font-mono font-bold text-[#ff2244]/20 mb-3">05</div>
              <h3 className="text-sm font-semibold mb-1">Expose</h3>
              <p className="text-xs text-gray-500">News, sanctions, corporate (two-pass)</p>
            </div>
            <div>
              <div className="text-4xl font-mono font-bold text-[#aa55ff]/20 mb-3">06</div>
              <h3 className="text-sm font-semibold mb-1">Measure</h3>
              <p className="text-xs text-gray-500">9-axis radar, dual scoring</p>
            </div>
          </div>
        </div>
      </Section>

      {/* ═══════════════════ Section 5: MOCK RESULT PREVIEW ═══════════════════ */}
      <Section className="py-32">
        <div className="max-w-3xl mx-auto px-6">
          <h2 className="text-3xl md:text-4xl font-bold text-center mb-16 font-['Instrument_Sans',sans-serif]">
            What you'll see
          </h2>

          <div className="bg-[#12121a] border border-[#1e1e2e] rounded-xl p-6 md:p-8 max-w-lg mx-auto">
            <div className="flex items-center gap-4 mb-5">
              <GenerativeAvatar
                seed={{ email_hash: 314159, ...DEFAULT_SEED_PROPS }}
                size={56}
                score={34}
              />
              <div>
                <div className="font-semibold">John Smith</div>
                <div className="text-xs text-gray-500 font-mono">john.smith@gmail.com</div>
              </div>
            </div>

            <div className="flex gap-6 mb-5">
              <div>
                <div className="text-[10px] text-gray-500 uppercase tracking-wider mb-1">Exposure</div>
                <div className="flex items-center gap-2">
                  <div className="text-xl font-mono font-bold text-[#ff8800]">34</div>
                  <div className="w-24 bg-[#1e1e2e] rounded-full h-1.5">
                    <div className="h-full bg-[#ff8800] rounded-full" style={{ width: '34%' }} />
                  </div>
                </div>
              </div>
              <div>
                <div className="text-[10px] text-gray-500 uppercase tracking-wider mb-1">Threat</div>
                <div className="flex items-center gap-2">
                  <div className="text-xl font-mono font-bold text-[#3388ff]">22</div>
                  <div className="w-24 bg-[#1e1e2e] rounded-full h-1.5">
                    <div className="h-full bg-[#3388ff] rounded-full" style={{ width: '22%' }} />
                  </div>
                </div>
              </div>
            </div>

            {/* Persona + location + photos */}
            <div className="flex flex-wrap items-center gap-3 mb-4 text-xs text-gray-400">
              <span className="bg-[#1e1e2e] rounded-full px-2.5 py-1 text-[#3388ff]">@jsmith · Primary · 12 platforms</span>
              <span className="bg-[#1e1e2e] rounded-full px-2.5 py-1">📍 San Francisco, US</span>
              <span className="bg-[#1e1e2e] rounded-full px-2.5 py-1">📷 4 photos</span>
            </div>

            <div className="space-y-2.5 mb-4">
              <div className="flex items-center gap-2 text-sm">
                <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-[#ff2244]/20 text-[#ff2244]">high</span>
                <span className="text-gray-300">1 breach found (LinkedIn 2021)</span>
              </div>
              <div className="flex items-center gap-2 text-sm">
                <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-[#ffcc00]/20 text-[#ffcc00]">medium</span>
                <span className="text-gray-300">12 social accounts detected</span>
              </div>
              <div className="flex items-center gap-2 text-sm">
                <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-[#ffcc00]/20 text-[#ffcc00]">medium</span>
                <span className="text-gray-300">Username "jsmith" reused on 5 platforms</span>
              </div>
              <div className="flex items-center gap-2 text-sm">
                <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-[#3388ff]/20 text-[#3388ff]">info</span>
                <span className="text-gray-300">9-axis fingerprint: high account spread, moderate security</span>
              </div>
            </div>

            <div className="relative">
              <div className="space-y-2 blur-sm select-none">
                {[1,2,3].map(i => (
                  <div key={i} className="flex items-center gap-2 text-sm">
                    <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-gray-800 text-gray-600">low</span>
                    <span className="text-gray-600">Additional finding — sign up to view</span>
                  </div>
                ))}
              </div>
              <div className="absolute inset-0 flex items-center justify-center">
                <a href="/setup"
                  className="bg-[#00ff88] text-black font-bold rounded-lg px-6 py-2.5 text-sm hover:bg-[#00ff88]/90 transition-all hover:scale-105 shadow-lg shadow-[#00ff88]/20">
                  See your full report — Free
                </a>
              </div>
            </div>
          </div>
        </div>
      </Section>

      {/* ═══════════════════ Section 6: WHO IT'S FOR ═══════════════════ */}
      <Section className="py-32">
        <div className="max-w-4xl mx-auto px-6">
          <h2 className="text-3xl md:text-4xl font-bold text-center mb-16 font-['Instrument_Sans',sans-serif]">
            Built for
          </h2>

          <div className="grid md:grid-cols-3 gap-6">
            {AUDIENCES.map(a => (
              <div key={a.label} className="bg-[#12121a] border border-[#1e1e2e] rounded-xl p-6 text-center hover:border-[#1e1e2e] transition-all">
                <h3 className="text-lg font-semibold mb-2">{a.label}</h3>
                <p className="text-sm text-gray-400 mb-1">{a.desc}</p>
                <p className="text-sm text-[#00ff88] font-mono mb-5">{a.price}</p>
                <a href={a.href}
                  className="inline-block text-sm font-semibold border border-[#1e1e2e] text-gray-300 hover:border-gray-500 rounded-lg px-5 py-2 transition-colors">
                  {a.cta}
                </a>
              </div>
            ))}
          </div>
        </div>
      </Section>

      {/* ═══════════════════ Section 7: TRUST ═══════════════════ */}
      <Section className="py-20">
        <div className="max-w-4xl mx-auto px-6">
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4 text-center">
            {[
              { value: '117', label: 'OSINT sources' },
              { value: '9-axis', label: 'Behavioral radar' },
              { value: '2-pass', label: 'Intelligence pipeline' },
              { value: '40+', label: 'Sanctions lists' },
              { value: 'GDPR', label: 'Aware architecture' },
              { value: 'AES-256', label: 'Encrypted keys' },
            ].map(t => (
              <div key={t.label} className="bg-[#12121a] border border-[#1e1e2e] rounded-lg py-3 px-2">
                <div className="text-sm font-mono font-bold text-[#00ff88]">{t.value}</div>
                <div className="text-[10px] text-gray-500 mt-0.5">{t.label}</div>
              </div>
            ))}
          </div>
          <p className="text-sm text-gray-600 text-center mt-4">
            Built in Luxembourg <span className="inline-block">🇱🇺</span> · Open source · On-premise ready · Your data stays yours.
          </p>
        </div>
      </Section>

      {/* ═══════════════════ Section 8: TECH STACK ═══════════════════ */}
      <Section className="py-12">
        <div className="max-w-3xl mx-auto px-6 text-center">
          <div className="flex flex-wrap justify-center gap-3">
            {['FastAPI', 'Celery', 'PostgreSQL', 'Redis', 'React', 'D3.js', 'Docker'].map(t => (
              <span key={t} className="text-[11px] font-mono text-gray-500 bg-[#12121a] border border-[#1e1e2e] rounded-full px-3 py-1">
                {t}
              </span>
            ))}
          </div>
        </div>
      </Section>

      {/* ═══════════════════ Section 9: FINAL CTA ═══════════════════ */}
      <Section className="py-32">
        <div className="max-w-3xl mx-auto px-6 text-center">
          <h2 className="text-3xl md:text-4xl font-bold mb-6 font-['Instrument_Sans',sans-serif]">
            What does an attacker already know about{' '}
            <span className="text-[#00ff88]">you</span>?
          </h2>

          <div className="flex justify-center mb-4">
            <ScanForm email={email} setEmail={setEmail} loading={loading} error={error} onSubmit={handleQuickScan} />
          </div>

          <p className="text-sm text-gray-600">
            Free. No credit card. Results in 30 seconds.
          </p>
        </div>
      </Section>

      {/* ─── Footer ─── */}
      <footer className="border-t border-[#1e1e2e] py-12">
        <div className="max-w-5xl mx-auto px-6">
          <div className="flex flex-col md:flex-row items-center justify-between gap-4">
            <div className="flex items-center gap-2">
              <Shield className="w-5 h-5 text-[#00ff88]" />
              <span className="font-bold font-['Instrument_Sans',sans-serif]">xpose</span>
              <span className="text-xs text-gray-600 font-mono ml-2">v0.70.0</span>
            </div>
            <p className="text-xs text-gray-600 font-mono text-center">
              Identity Threat Intelligence · 117 Sources · Two-Pass Pipeline · Open Source
            </p>
            <div className="flex items-center gap-4 text-xs text-gray-500">
              <a href="/architecture" className="hover:text-white transition-colors">How it works</a>
              <a href="/architecture#roadmap" className="hover:text-white transition-colors">Roadmap</a>
              <a href="https://github.com/nabz0r/xposeTIP" className="hover:text-white transition-colors">GitHub</a>
              <a href="/login" className="hover:text-white transition-colors">Sign in</a>
            </div>
          </div>
        </div>
      </footer>
    </div>
  )
}
