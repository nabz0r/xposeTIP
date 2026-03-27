import { useEffect, useRef } from 'react'
import { Link } from 'react-router-dom'
import { Shield, Zap, BookOpen, ArrowRight, ChevronRight } from 'lucide-react'

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
        <p className="text-sm text-gray-400 leading-relaxed">{children}</p>
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
              <Rule num="01" title="Consent First">
                You scan yourself. Or someone who asked you to.
                No mass surveillance. No unconsented profiling.
                Every scan requires a purpose.
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
                  <div className="flex items-start gap-3">
                    <ChevronRight className="w-4 h-4 text-[#3388ff] shrink-0 mt-0.5" />
                    <span>Data-driven scrapers (no code per source — just JSON config)</span>
                  </div>
                  <div className="flex items-start gap-3">
                    <ChevronRight className="w-4 h-4 text-[#3388ff] shrink-0 mt-0.5" />
                    <span>Single PostgreSQL (no distributed cluster)</span>
                  </div>
                  <div className="flex items-start gap-3">
                    <ChevronRight className="w-4 h-4 text-[#3388ff] shrink-0 mt-0.5" />
                    <span>Celery + Redis (not Kafka + ZooKeeper + 7 brokers)</span>
                  </div>
                  <div className="flex items-start gap-3">
                    <ChevronRight className="w-4 h-4 text-[#3388ff] shrink-0 mt-0.5" />
                    <span>Pixel art avatars (5.4B combinations, zero GPU, zero API call)</span>
                  </div>
                  <div className="flex items-start gap-3">
                    <ChevronRight className="w-4 h-4 text-[#3388ff] shrink-0 mt-0.5" />
                    <span>Every architectural decision asks: "is this the lightest way?"</span>
                  </div>
                </div>
              </div>

              <div className="reveal opacity-0 translate-y-8 transition-all duration-700 bg-[#12121a] border border-[#1e1e2e] rounded-xl p-6 md:p-8">
                <h3 className="text-sm font-bold text-[#3388ff] uppercase tracking-wider mb-6">
                  The Math
                </h3>
                <div className="grid grid-cols-2 gap-8">
                  <div>
                    <p className="text-xs text-gray-500 uppercase tracking-wider mb-4">Typical Enterprise Scan</p>
                    <div className="space-y-3">
                      <Stat value="~$0.50" label="per scan (compute + API)" color="#ff8800" />
                      <Stat value="~2g" label="CO2 per scan" color="#ff8800" />
                      <Stat value="12+" label="containers, 3 managed services" color="#ff8800" />
                    </div>
                  </div>
                  <div>
                    <p className="text-xs text-gray-500 uppercase tracking-wider mb-4">xpose Scan</p>
                    <div className="space-y-3">
                      <Stat value="~$0.001" label="per scan (local compute)" color="#00ff88" />
                      <Stat value="~0.02g" label="CO2 per scan" color="#00ff88" />
                      <Stat value="5" label="containers, 0 managed services" color="#00ff88" />
                    </div>
                  </div>
                </div>
                <p className="text-center text-sm text-gray-500 mt-6 font-mono">
                  100x cheaper. 100x greener. Same depth.
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
                {
                  quote: '"Your score is 42 because you reuse the same username across 12 platforms. Here\'s why that\'s risky: an attacker who compromises one account can try the same credentials on all 12."',
                },
                {
                  quote: '"We found your email in the LinkedIn 2021 breach. This means your password hash was exposed. Even if you changed your LinkedIn password, attackers test these credentials on every other service."',
                },
                {
                  quote: '"Your GitHub profile reveals your real name, employer, location, and timezone. This is enough for a targeted phishing email that mentions your company by name."',
                },
              ].map((ex, i) => (
                <div key={i} className="reveal opacity-0 translate-y-8 transition-all duration-700 bg-[#12121a] border border-[#1e1e2e] rounded-xl p-6">
                  <p className="text-sm text-gray-300 leading-relaxed italic">{ex.quote}</p>
                </div>
              ))}

              <div className="reveal opacity-0 translate-y-8 transition-all duration-700 mt-8 text-center">
                <p className="text-gray-400 leading-relaxed">
                  We don't just scan. We teach.<br />
                  <span className="text-[#ffcc00]">The goal isn't to make you dependent on xpose.
                  It's to make you not need xpose anymore.</span>
                </p>
              </div>
            </div>
          </Pillar>
        </section>

        {/* Footer */}
        <footer className="reveal opacity-0 translate-y-8 transition-all duration-700 border-t border-[#1e1e2e] pt-16 text-center">
          <p className="text-gray-500 text-sm mb-6">
            Built in Luxembourg. Open OSINT. Ethical by design. Green by philosophy.
          </p>
          <div className="flex items-center justify-center gap-6">
            <Link to="/welcome"
              className="flex items-center gap-2 text-sm text-[#00ff88] hover:underline">
              Back to product <ArrowRight className="w-4 h-4" />
            </Link>
            <Link to="/architecture"
              className="flex items-center gap-2 text-sm text-gray-400 hover:text-white transition-colors">
              Read the architecture <ArrowRight className="w-4 h-4" />
            </Link>
          </div>
        </footer>

      </div>
    </div>
  )
}
