import { Radar } from 'lucide-react'
import GenerativeAvatar from '../GenerativeAvatar'
import ScanForm from './ScanForm'
import { scoreColor, sevColor, hashEmail } from './constants'

export default function HeroSection({ email, setEmail, loading, error, onSubmit, quickResult, pollCount, phaseMsg }) {
  return (
    <>
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
              The Identity Layer · Free lookup
            </div>

            <h1 className="text-5xl md:text-6xl lg:text-7xl font-bold tracking-tight leading-[1.1] mb-6 font-['Instrument_Sans',sans-serif]">
              The threat is not<br />
              the indicator.<br />
              <span className="text-gray-500">It's the person behind it.</span>
            </h1>

            <p className="text-gray-300 text-lg mb-8 max-w-lg leading-relaxed">
              xposeTIP treats identity as a layer.{' '}
              <span className="text-white font-semibold">Behavioral. Persistent. Foundational.</span>{' '}
              Type your email below — see what the internet knows about you.
            </p>

            <div className="flex flex-wrap gap-3 text-[11px] font-mono text-gray-500 mb-8">
              <span className="bg-[#1e1e2e] px-2.5 py-1 rounded-full">170 OSINT sources</span>
              <span className="bg-[#1e1e2e] px-2.5 py-1 rounded-full">11-axis behavioral fingerprint</span>
              <span className="bg-[#1e1e2e] px-2.5 py-1 rounded-full">🇱🇺 Made in Luxembourg</span>
            </div>

            <div className="mb-8">
              <ScanForm email={email} setEmail={setEmail} loading={loading} error={error} onSubmit={onSubmit} />
            </div>

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

          {/* Right — Composite identity report screenshot (anonymized, real shape) */}
          <div className="hidden lg:block relative">
            <img
              src="/hero/identity-report-composite.webp"
              alt="xposeTIP identity report — composite from real anonymized scans"
              className="rounded-xl border border-[#1e1e2e] shadow-2xl shadow-[#00ff88]/5 max-w-md w-full"
              loading="eager"
              fetchPriority="high"
            />
            {/* Subtle ambient glow */}
            <div className="absolute -inset-4 bg-[#00ff88]/5 rounded-2xl blur-2xl -z-10" />
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
