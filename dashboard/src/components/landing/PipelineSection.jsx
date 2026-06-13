import { Link } from 'react-router-dom'
import Section from '../shared/Section'
import { SOURCE_COUNT } from './constants'

export default function PipelineSection() {
  return (
    <Section className="py-32">
      <div className="max-w-4xl mx-auto px-6">
        <h2 className="text-3xl md:text-4xl font-bold text-center mb-6 font-['Instrument_Sans',sans-serif]">
          Three steps. One identity.
        </h2>
        <p className="text-center text-gray-500 text-sm mb-16 max-w-lg mx-auto">
          No configuration. No API keys. Enter an email and let the pipeline work.
        </p>

        <div className="grid md:grid-cols-3 gap-8">
          <div className="relative">
            <div className="text-5xl font-mono font-bold text-[#00ff88]/15 mb-4">01</div>
            <h3 className="text-lg font-semibold mb-3 text-[#00ff88]">Discover</h3>
            <p className="text-sm text-gray-400 leading-relaxed mb-3">
              Scan {SOURCE_COUNT} sources in parallel for accounts, breaches, usernames, archives, and metadata.
            </p>
            <p className="text-xs text-gray-600">
              Social networks, dev platforms, gaming, breach databases, people search engines — everything tied to that email.
            </p>
            {/* Connector arrow (hidden on mobile) */}
            <div className="hidden md:block absolute top-8 -right-4 text-gray-700 text-2xl">→</div>
          </div>

          <div className="relative">
            <div className="text-5xl font-mono font-bold text-[#ff8800]/15 mb-4">02</div>
            <h3 className="text-lg font-semibold mb-3 text-[#ff8800]">Enrich</h3>
            <p className="text-sm text-gray-400 leading-relaxed mb-3">
              Once a name is resolved with high confidence, search global news archives, 40+ sanctions lists, corporate registries, and court records in the US, France, and the UK.
            </p>
            <p className="text-xs text-gray-600">
              Five independent layers — media, sanctions, corporate, legal, geographic — so errors never cascade.
            </p>
            <div className="hidden md:block absolute top-8 -right-4 text-gray-700 text-2xl">→</div>
          </div>

          <div>
            <div className="text-5xl font-mono font-bold text-[#ff2244]/15 mb-4">03</div>
            <h3 className="text-lg font-semibold mb-3 text-[#ff2244]">Identify</h3>
            <p className="text-sm text-gray-400 leading-relaxed mb-3">
              Build an 11-axis behavioral fingerprint, cluster digital personas, and measure exposure in identifying bits — how much of what makes you unique the open web has already resolved. Every finding is sourced and timestamped.
            </p>
            <p className="text-xs text-gray-600">
              A human is ~33 bits of information. The ledger shows which bits are out, where they leaked, and what to do about each one.
            </p>
          </div>
        </div>

        <div className="text-center mt-12">
          <Link
            to="/doc/engine"
            className="inline-flex items-center gap-2 text-[#00ff88] hover:text-[#00ff88]/80 text-sm font-mono transition-colors"
          >
            See the exact engine pathway
            <span aria-hidden>→</span>
          </Link>
        </div>
      </div>
    </Section>
  )
}
