import Section from '../shared/Section'
import { AUDIENCES } from './constants'

export default function PricingSection() {
  return (
    <Section className="py-32">
      <div className="max-w-4xl mx-auto px-6">
        <h2 className="text-3xl md:text-4xl font-bold text-center mb-4 font-['Instrument_Sans',sans-serif]">
          Pricing
        </h2>
        <p className="text-center text-gray-500 text-sm mb-2 max-w-lg mx-auto">
          Start free. Scale as your operations grow.
        </p>
        <p className="text-center text-gray-600 text-xs mb-16 max-w-lg mx-auto italic">
          Starter and Team are accepting waitlist signups. Free is available immediately.
        </p>

        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-4">
          {AUDIENCES.map(a => (
            <div key={a.label} className="bg-[#12121a] border border-[#1e1e2e] rounded-xl p-6 text-center hover:border-[#1e1e2e] transition-all">
              <h3 className="text-lg font-semibold mb-2">{a.label}</h3>
              <p className="text-sm text-gray-400 mb-1">{a.desc}</p>
              <p className="text-sm text-[#00ff88] font-mono mb-4">{a.price}</p>
              {a.features && (
                <ul className="text-left text-xs text-gray-500 space-y-1.5 mb-5">
                  {a.features.map((f, i) => (
                    <li key={i} className="flex items-start gap-2">
                      <span className="text-[#00ff88] mt-0.5">+</span>
                      <span>{f}</span>
                    </li>
                  ))}
                </ul>
              )}
              <a href={a.href}
                className="inline-block text-sm font-semibold border border-[#1e1e2e] text-gray-300 hover:border-gray-500 rounded-lg px-5 py-2 transition-colors">
                {a.cta}
              </a>
            </div>
          ))}
        </div>
      </div>
    </Section>
  )
}
