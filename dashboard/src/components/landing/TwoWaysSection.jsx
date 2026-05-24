import Section from '../shared/Section'
import { Briefcase, Layers } from 'lucide-react'

export default function TwoWaysSection() {
  return (
    <Section className="py-32">
      <div className="max-w-5xl mx-auto px-6">
        <h2 className="text-3xl md:text-4xl font-bold text-center mb-4 font-['Instrument_Sans',sans-serif]">
          Two ways to engage
        </h2>
        <p className="text-center text-gray-500 text-sm mb-16 max-w-lg mx-auto">
          Use the platform yourself — or have us deliver the analysis as a service.
        </p>

        <div className="grid md:grid-cols-2 gap-6">
          {/* Play 1 — Consulting */}
          <div className="bg-[#12121a] border border-[#aa66ff]/30 rounded-xl p-8">
            <div className="flex items-center gap-3 mb-5">
              <div className="w-10 h-10 rounded-xl bg-[#aa66ff]/15 flex items-center justify-center">
                <Briefcase className="w-5 h-5 text-[#aa66ff]" />
              </div>
              <div>
                <div className="text-[10px] uppercase tracking-wider text-[#aa66ff] font-mono">Productized consulting</div>
                <h3 className="text-xl font-semibold">Identity Intelligence Reports</h3>
              </div>
            </div>

            <p className="text-sm text-gray-400 leading-relaxed mb-5">
              For due diligence firms, law firms, family offices, cyber insurance underwriters, and VC diligence teams. Turnaround in days, not weeks. Capped engagements — depth over volume.
            </p>

            <div className="space-y-2.5 mb-6 text-sm">
              {[
                ['Quick Profile', '€2 500', '48h · 1 identity'],
                ['Identity Assessment', '€6 500', '5d · full PDF report'],
                ['Deep Investigation', '€15 000', '10d · up to 5 connected identities'],
                ['Strategic Briefing', '€25–40K', '3-4w · custom, board-ready'],
              ].map(([tier, price, scope]) => (
                <div key={tier} className="flex items-baseline justify-between gap-3 py-1.5 border-b border-[#1e1e2e] last:border-0">
                  <span className="text-gray-300 font-medium">{tier}</span>
                  <span className="text-[#aa66ff] font-mono font-bold shrink-0">{price}</span>
                  <span className="text-[10px] text-gray-600 font-mono truncate hidden sm:inline">{scope}</span>
                </div>
              ))}
            </div>

            <a
              href="mailto:contact@redbird.co.com?subject=xposeTIP%20Identity%20Intelligence%20Report%20inquiry"
              className="inline-block text-sm font-semibold bg-[#aa66ff]/15 text-[#aa66ff] border border-[#aa66ff]/40 hover:bg-[#aa66ff]/25 rounded-lg px-5 py-2.5 transition-colors"
            >
              Talk to us
            </a>
          </div>

          {/* Play 2 — SaaS */}
          <div className="bg-[#12121a] border border-[#00ff88]/30 rounded-xl p-8">
            <div className="flex items-center gap-3 mb-5">
              <div className="w-10 h-10 rounded-xl bg-[#00ff88]/15 flex items-center justify-center">
                <Layers className="w-5 h-5 text-[#00ff88]" />
              </div>
              <div>
                <div className="text-[10px] uppercase tracking-wider text-[#00ff88] font-mono">Self-service platform</div>
                <h3 className="text-xl font-semibold">xposeTIP Cloud</h3>
              </div>
            </div>

            <p className="text-sm text-gray-400 leading-relaxed mb-5">
              Run scans yourself. Build your own workspace. API access for SIEM/SOAR integration on Team plan and above. Core engine open source — AGPL-3.0.
            </p>

            <div className="space-y-2.5 mb-6 text-sm">
              {[
                ['Free', '€0', '25 scans / month'],
                ['Starter', '€49/mo', '250 full scans · 170 sources'],
                ['Team', '€299/mo', '2 000 scans · 5 seats · API'],
                ['Enterprise', 'From €2 500/mo', 'Multi-tenant · SSO · SLA'],
              ].map(([tier, price, scope]) => (
                <div key={tier} className="flex items-baseline justify-between gap-3 py-1.5 border-b border-[#1e1e2e] last:border-0">
                  <span className="text-gray-300 font-medium">{tier}</span>
                  <span className="text-[#00ff88] font-mono font-bold shrink-0">{price}</span>
                  <span className="text-[10px] text-gray-600 font-mono truncate hidden sm:inline">{scope}</span>
                </div>
              ))}
            </div>

            <a
              href="/setup"
              className="inline-block text-sm font-semibold bg-[#00ff88] text-black hover:bg-[#00ff88]/90 rounded-lg px-5 py-2.5 transition-colors"
            >
              Start free
            </a>
          </div>
        </div>
      </div>
    </Section>
  )
}
