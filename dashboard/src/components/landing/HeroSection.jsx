import { Radar, Shield } from 'lucide-react'
import GenerativeAvatar from '../GenerativeAvatar'
import ScanForm from './ScanForm'
import { DEMO_AVATARS, DEFAULT_SEED_PROPS, scoreColor, sevColor, hashEmail } from './constants'

export default function HeroSection({ email, setEmail, loading, error, onSubmit, quickResult, pollCount, phaseMsg }) {
  return (
    <>
      {/* ─── Nav ─── */}
      <nav className="fixed top-0 w-full z-50 border-b border-[#1e1e2e]/50 bg-[#0a0a0f]/80 backdrop-blur-xl px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Shield className="w-6 h-6 text-[#00ff88]" />
          <span className="text-xl font-bold tracking-tight font-['Instrument_Sans',sans-serif]">xpose</span>
          <span className="text-[10px] font-mono text-gray-600 ml-1">TIP</span>
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
              Threat Identity Platform · Free scan
            </div>

            <h1 className="text-5xl md:text-6xl lg:text-7xl font-bold tracking-tight leading-[1.1] mb-6 font-['Instrument_Sans',sans-serif]">
              The threat is not<br />
              the indicator.<br />
              <span className="text-gray-500">It's the person behind it.</span>
            </h1>

            <p className="text-gray-400 text-lg mb-4 max-w-lg leading-relaxed">
              The threat intelligence industry is drowning in noise. 100,000 IOCs a day.
              IPs that change. Blocklists stale by morning.
            </p>
            <p className="text-gray-300 text-lg mb-6 max-w-lg leading-relaxed">
              xposeTIP doesn't store indicators.<br />
              <span className="text-white font-semibold">xposeTIP builds identities.</span>
            </p>

            <div className="flex flex-wrap gap-3 text-[11px] font-mono text-gray-500 mb-8">
              <span className="bg-[#1e1e2e] px-2.5 py-1 rounded-full">1 email → 1 complete persona</span>
              <span className="bg-[#1e1e2e] px-2.5 py-1 rounded-full">9-axis behavioral fingerprint</span>
              <span className="bg-[#1e1e2e] px-2.5 py-1 rounded-full">124 OSINT sources</span>
            </div>

            <div className="mb-8">
              <ScanForm email={email} setEmail={setEmail} loading={loading} error={error} onSubmit={onSubmit} />
            </div>

            <p className="text-sm text-gray-600">
              Enter any email. In 2 minutes, you'll see the person behind it.
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
                        <span className="text-gray-600">Identity detail hidden — create account to view</span>
                      </div>
                    ))}
                  </div>
                  <div className="absolute inset-0 flex items-center justify-center">
                    <a href={quickResult.upsell?.cta_url || `/setup?email=${encodeURIComponent(email)}`}
                       className="bg-[#00ff88] text-black font-bold rounded-lg px-6 py-3 text-sm hover:bg-[#00ff88]/90 transition-all hover:scale-105 shadow-lg shadow-[#00ff88]/20">
                      See full identity report — Free
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
    </>
  )
}
