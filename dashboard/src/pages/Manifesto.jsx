import { useEffect, useRef } from 'react'
import { Link } from 'react-router-dom'
import { Shield, Zap, BookOpen, Lock, ArrowRight, ChevronRight, X } from 'lucide-react'

function useScrollReveal() {
  const ref = useRef(null)
  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach(entry => {
          if (entry.isIntersecting) {
            entry.target.classList.add('opacity-100', 'translate-y-0')
            entry.target.classList.remove('opacity-0', 'translate-y-8')
          }
        })
      },
      { threshold: 0.1 }
    )
    const els = ref.current?.querySelectorAll('.reveal')
    els?.forEach(el => observer.observe(el))
    return () => observer.disconnect()
  }, [])
  return ref
}

function Pillar({ num, icon: Icon, color, title, children }) {
  return (
    <div className="reveal opacity-0 translate-y-8 transition-all duration-700">
      <div className="flex items-center gap-3 mb-8">
        <div className="w-10 h-10 rounded-lg flex items-center justify-center" style={{ backgroundColor: color + '15' }}>
          <Icon className="w-5 h-5" style={{ color }} />
        </div>
        <span className="text-xs font-mono text-gray-500">PILLAR {num}</span>
      </div>
      <h2 className="text-2xl md:text-3xl font-bold mb-8 font-['Instrument_Sans',sans-serif]" style={{ color }}>
        {title}
      </h2>
      {children}
    </div>
  )
}

function Rule({ num, title, children }) {
  return (
    <div className="flex gap-4 mb-6">
      <span className="text-lg font-mono font-bold text-gray-700 shrink-0 w-8">{num}</span>
      <div>
        <h3 className="text-sm font-bold text-white uppercase tracking-wider mb-1">{title}</h3>
        <div className="text-sm text-gray-400 leading-relaxed">{children}</div>
      </div>
    </div>
  )
}

function Stat({ value, label, color }) {
  return (
    <div className="text-center">
      <div className="text-2xl font-mono font-bold" style={{ color }}>{value}</div>
      <div className="text-[10px] text-gray-500 mt-1">{label}</div>
    </div>
  )
}

export default function Manifesto() {
  const containerRef = useScrollReveal()

  return (
    <div ref={containerRef} className="min-h-screen bg-[#0a0a0f] text-white">
      {/* Nav */}
      <nav className="fixed top-0 left-0 right-0 z-50 bg-[#0a0a0f]/90 backdrop-blur-sm border-b border-[#1e1e2e]">
        <div className="max-w-4xl mx-auto px-6 h-14 flex items-center justify-between">
          <Link to="/welcome" className="flex items-center gap-2">
            <Shield className="w-4 h-4 text-[#00ff88]" />
            <span className="font-bold text-sm">xpose</span>
            <span className="text-[10px] font-mono text-gray-600">TIP</span>
          </Link>
          <div className="flex items-center gap-4 text-xs text-gray-500">
            <Link to="/welcome" className="hover:text-white transition-colors">Product</Link>
            <Link to="/architecture" className="hover:text-white transition-colors">Architecture</Link>
            <Link to="/login" className="hover:text-white transition-colors">Sign in</Link>
          </div>
        </div>
      </nav>

      <div className="max-w-3xl mx-auto px-6 pt-32 pb-20">

        {/* Hero */}
        <section className="reveal opacity-0 translate-y-8 transition-all duration-700 mb-32 text-center">
          <h1 className="text-4xl md:text-5xl font-bold mb-6 font-['Instrument_Sans',sans-serif] leading-tight">
            We build mirrors,<br />
            <span className="text-[#00ff88]">not weapons.</span>
          </h1>
          <p className="text-lg text-gray-400 max-w-xl mx-auto leading-relaxed">
            xpose reveals what the internet already knows about you.
            Not to exploit it. To fix it.
          </p>
        </section>

        {/* Pillar 1 — Ethical OSINT */}
        <section className="mb-32">
          <Pillar num="01" icon={Shield} color="#00ff88" title="Ethical OSINT">
            <div className="bg-[#12121a] border border-[#1e1e2e] rounded-xl p-6 md:p-8">
              <Rule num="01" title="Consent Model">
                <p className="mb-2"><span className="text-white font-semibold">Self-scan:</span> Anyone can scan their own email. Free, no justification needed.</p>
                <p className="mb-2"><span className="text-white font-semibold">Third-party scan:</span> Requires documented consent — a signed DPA, an employer policy, or explicit written authorization from the data subject.</p>
                <p className="mb-2"><span className="text-white font-semibold">Bulk scan:</span> Permitted for organizations scanning their own workforce under GDPR Article 6(1)(f) legitimate interest — never for profiling external individuals.</p>
                <p>No scan is ever anonymous to us. Every scan is logged with who authorized it, when, and why.</p>
              </Rule>
              <Rule num="02" title="Transparency">
                Every finding shows its source. Every score explains its reasoning.
                No black boxes. No "trust us" scores.
                You see exactly what we see.
              </Rule>
              <Rule num="03" title="Purpose Limitation">
                xpose finds exposure to help you reduce it.
                Every finding comes with a remediation action.
                We're a shield, not a sword.
              </Rule>
              <Rule num="04" title="Right to Delete">
                Request deletion. We purge everything.
                Not soft delete. Not "archived." Gone.
                Your data, your choice.
              </Rule>
              <Rule num="05" title="No Dark Patterns">
                No upsell scare tactics. No inflated scores to push premium plans.
                A score of 6 means you're fine. We tell you that.
              </Rule>
            </div>

            {/* Rule 06 — Red Lines */}
            <div className="reveal opacity-0 translate-y-8 transition-all duration-700 mt-6 bg-[#0a0a0f] border-2 border-[#ff2244]/30 rounded-xl p-6 md:p-8">
              <div className="flex items-center gap-3 mb-5">
                <X className="w-5 h-5 text-[#ff2244]" />
                <h3 className="text-sm font-bold text-[#ff2244] uppercase tracking-wider">06 — We Will Never</h3>
              </div>
              <ul className="space-y-3 text-sm font-mono text-gray-300">
                {[
                  'Accept contracts for unconsented pre-employment screening',
                  'Sell, license, or share scan data with data brokers, advertisers, or intelligence agencies',
                  'Accept military, mass surveillance, or law enforcement contracts for profiling civilians',
                  'Build facial recognition, social scoring, or predictive profiling features',
                  'Monetize scan results, even anonymized or aggregated',
                  'Retain data for users who delete their account — purge is cryptographic, not soft delete',
                  'Comply with data requests from authoritarian regimes, regardless of legal pressure',
                ].map((line, i) => (
                  <li key={i} className="flex items-start gap-3">
                    <X className="w-3.5 h-3.5 text-[#ff2244] shrink-0 mt-0.5" />
                    <span>{line}</span>
                  </li>
                ))}
              </ul>
              <p className="text-xs text-gray-500 mt-6 leading-relaxed">
                These aren't aspirational. They're hardcoded. If a future version of xpose violates any of these,
                fork the repo and call us out. The code is MIT-licensed for exactly this reason.
              </p>
            </div>
          </Pillar>
        </section>

        {/* Pillar 2 — Green Intelligence */}
        <section className="mb-32">
          <Pillar num="02" icon={Zap} color="#3388ff" title="Green Intelligence">
            <div className="space-y-8">
              <div className="reveal opacity-0 translate-y-8 transition-all duration-700">
                <p className="text-gray-400 leading-relaxed mb-6">
                  The cybersecurity industry runs 256GB RAM clusters to grep logs.
                  We run 120 OSINT scrapers, PageRank, Markov chains, and a rules engine
                  on a 7-year-old MacBook. 50 watts.
                </p>
              </div>

              <div className="reveal opacity-0 translate-y-8 transition-all duration-700 bg-[#12121a] border border-[#1e1e2e] rounded-xl p-6 md:p-8">
                <h3 className="text-sm font-bold text-[#3388ff] uppercase tracking-wider mb-4">
                  The Amiga 500 Philosophy
                </h3>
                <p className="text-sm text-gray-400 leading-relaxed mb-6">
                  In 1987, demoscene coders made art with 512KB of RAM that
                  still amazes today. Not because they had less — because
                  constraints breed creativity.
                </p>
                <div className="space-y-3 text-sm text-gray-300">
                  {[
                    'Data-driven scrapers (no code per source — just JSON config)',
                    'Single PostgreSQL (no distributed cluster)',
                    'Celery + Redis (not Kafka + ZooKeeper + 7 brokers)',
                    'Pixel art avatars (5.4B combinations, zero GPU, zero API call)',
                    'Every architectural decision asks: "is this the lightest way?"',
                  ].map((item, i) => (
                    <div key={i} className="flex items-start gap-3">
                      <ChevronRight className="w-4 h-4 text-[#3388ff] shrink-0 mt-0.5" />
                      <span>{item}</span>
                    </div>
                  ))}
                </div>
              </div>

              <div className="reveal opacity-0 translate-y-8 transition-all duration-700 bg-[#12121a] border border-[#1e1e2e] rounded-xl p-6 md:p-8">
                <h3 className="text-sm font-bold text-[#3388ff] uppercase tracking-wider mb-4">
                  Our Benchmark
                </h3>
                <p className="text-xs text-gray-500 mb-4">Measured on a 2019 MacBook Pro, 50W TDP</p>
                <div className="grid grid-cols-2 gap-8">
                  <div>
                    <p className="text-xs text-gray-500 uppercase tracking-wider mb-4">xpose Scan</p>
                    <div className="space-y-3">
                      <Stat value="~90s" label="of compute per scan" color="#00ff88" />
                      <Stat value="~1.25 Wh" label="energy per scan" color="#00ff88" />
                      <Stat value="~0.9g" label="CO2 (EU grid avg 722g/kWh)" color="#00ff88" />
                      <Stat value="5" label="containers, 0 managed services" color="#00ff88" />
                    </div>
                  </div>
                  <div>
                    <p className="text-xs text-gray-500 uppercase tracking-wider mb-4">Typical Cloud OSINT</p>
                    <div className="space-y-3">
                      <Stat value="3-5 min" label="on m5.xlarge ($0.19/hr)" color="#ff8800" />
                      <Stat value="5-10x" label="energy footprint" color="#ff8800" />
                      <Stat value="+" label="Elasticsearch + API costs" color="#ff8800" />
                      <Stat value="12+" label="containers, 3+ managed services" color="#ff8800" />
                    </div>
                  </div>
                </div>
                <p className="text-center text-xs text-gray-600 mt-6 font-mono">
                  We don't claim 100x. We claim significantly less — and we show our math.
                </p>
              </div>
            </div>
          </Pillar>
        </section>

        {/* Pillar 3 — Education First */}
        <section className="mb-32">
          <Pillar num="03" icon={BookOpen} color="#ffcc00" title="Education First">
            <div className="space-y-6">
              <div className="reveal opacity-0 translate-y-8 transition-all duration-700">
                <p className="text-gray-400 leading-relaxed mb-8">
                  Most security tools show you a number and say "fix it."
                  xpose shows you <span className="text-white font-semibold">WHY</span>.
                </p>
              </div>

              {[
                '"Your score is 42 because you reuse the same username across 12 platforms. Here\'s why that\'s risky: an attacker who compromises one account can try the same credentials on all 12."',
                '"We found your email in the LinkedIn 2021 breach. This means your password hash was exposed. Even if you changed your LinkedIn password, attackers test these credentials on every other service."',
                '"Your GitHub profile reveals your real name, employer, location, and timezone. This is enough for a targeted phishing email that mentions your company by name."',
              ].map((quote, i) => (
                <div key={i} className="reveal opacity-0 translate-y-8 transition-all duration-700 bg-[#12121a] border border-[#1e1e2e] rounded-xl p-6">
                  <p className="text-sm text-gray-300 leading-relaxed italic">{quote}</p>
                </div>
              ))}

              <div className="reveal opacity-0 translate-y-8 transition-all duration-700 mt-8 text-center">
                <p className="text-gray-400 leading-relaxed">
                  We don't just scan. We teach.<br />
                  <span className="text-[#ffcc00]">The goal isn't to make you dependent on xpose.
                  It's to make you not need xpose anymore.</span>
                </p>
                <p className="text-xs text-gray-600 mt-3">
                  We measure success by how many people improve their score to A — not by how many people renew their subscription.
                </p>
              </div>
            </div>
          </Pillar>
        </section>

        {/* Pillar 4 — Data Commitment */}
        <section className="mb-32">
          <Pillar num="04" icon={Lock} color="#ff8800" title="Data Commitment">
            <div className="space-y-6">
              {[
                {
                  title: 'What we store',
                  color: '#ff8800',
                  items: [
                    'Scan results (findings, scores, graph) — tied to your workspace, encrypted at rest',
                    'Account credentials — hashed (bcrypt), never reversible',
                    'API keys — AES-256 encrypted (Fernet), never stored in plaintext',
                  ],
                },
                {
                  title: 'What we don\'t store',
                  color: '#00ff88',
                  items: [
                    'Raw HTML from scraped pages (discarded after extraction)',
                    'Passwords found in breaches (we note the breach, not the credential)',
                    'Biometric data (no facial recognition, no voiceprint, no behavioral biometrics)',
                  ],
                },
                {
                  title: 'Retention',
                  color: '#3388ff',
                  items: [
                    'Active accounts: data retained while account is active',
                    'Inactive accounts: scan data auto-purged after 12 months of inactivity',
                    'Deleted accounts: cryptographic purge within 72 hours — not soft delete, not "archived"',
                    'Workspace deletion: cascade purge of all targets, findings, identities, scans',
                  ],
                },
              ].map((section, i) => (
                <div key={i} className="reveal opacity-0 translate-y-8 transition-all duration-700 bg-[#12121a] border border-[#1e1e2e] rounded-xl p-6">
                  <h3 className="text-sm font-bold uppercase tracking-wider mb-4" style={{ color: section.color }}>
                    {section.title}
                  </h3>
                  <ul className="space-y-2">
                    {section.items.map((item, j) => (
                      <li key={j} className="flex items-start gap-3 text-sm text-gray-400">
                        <ChevronRight className="w-3.5 h-3.5 shrink-0 mt-0.5" style={{ color: section.color }} />
                        <span>{item}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              ))}

              <div className="reveal opacity-0 translate-y-8 transition-all duration-700 bg-[#0a0a0f] border-2 border-[#ff8800]/30 rounded-xl p-6">
                <h3 className="text-sm font-bold text-[#ff8800] uppercase tracking-wider mb-4">
                  What we will never do with your data
                </h3>
                <ul className="space-y-2 text-sm font-mono text-gray-300">
                  {[
                    'Train AI/ML models on scan results',
                    'Sell aggregated intelligence reports',
                    'Share data with any third party without explicit per-instance consent',
                    'Use scan patterns for competitive intelligence',
                  ].map((item, i) => (
                    <li key={i} className="flex items-start gap-3">
                      <X className="w-3.5 h-3.5 text-[#ff8800] shrink-0 mt-0.5" />
                      <span>{item}</span>
                    </li>
                  ))}
                </ul>
              </div>

              <div className="reveal opacity-0 translate-y-8 transition-all duration-700 text-center mt-4">
                <p className="text-sm text-gray-500 italic">
                  "Your scan data exists to protect you. The moment it stops serving that purpose, it should stop existing."
                </p>
              </div>
            </div>
          </Pillar>
        </section>

        {/* Footer */}
        <footer className="reveal opacity-0 translate-y-8 transition-all duration-700 border-t border-[#1e1e2e] pt-16 text-center">
          <p className="text-gray-500 text-sm mb-2">
            Built in Luxembourg — Ethical by constitution, not by marketing.
          </p>
          <p className="text-gray-600 text-xs mb-6">
            Open source (MIT) so you can verify every claim on this page.
          </p>
          <div className="flex items-center justify-center gap-6 mb-8">
            <Link to="/welcome"
              className="flex items-center gap-2 text-sm text-[#00ff88] hover:underline">
              Back to product <ArrowRight className="w-4 h-4" />
            </Link>
            <Link to="/architecture"
              className="flex items-center gap-2 text-sm text-gray-400 hover:text-white transition-colors">
              Read the architecture <ArrowRight className="w-4 h-4" />
            </Link>
          </div>
          <p className="text-[10px] text-gray-700 font-mono">Manifesto v2 — March 2026</p>
        </footer>

      </div>
    </div>
  )
}
