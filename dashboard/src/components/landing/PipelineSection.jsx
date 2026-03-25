import Section from '../shared/Section'

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
              Scan 117 sources in parallel for accounts, breaches, usernames, archives, and metadata.
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
              Once a name is resolved with high confidence, search global news archives, sanctions lists, and corporate registries.
            </p>
            <p className="text-xs text-gray-600">
              Three independent layers — media, compliance, corporate — so errors never cascade.
            </p>
            <div className="hidden md:block absolute top-8 -right-4 text-gray-700 text-2xl">→</div>
          </div>

          <div>
            <div className="text-5xl font-mono font-bold text-[#ff2244]/15 mb-4">03</div>
            <h3 className="text-lg font-semibold mb-3 text-[#ff2244]">Identify</h3>
            <p className="text-sm text-gray-400 leading-relaxed mb-3">
              Build a 9-axis behavioral fingerprint, cluster digital personas, and generate a concrete remediation plan.
            </p>
            <p className="text-xs text-gray-600">
              Not a dump of raw data. A multi-dimensional portrait with actionable next steps.
            </p>
          </div>
        </div>
      </div>
    </Section>
  )
}
