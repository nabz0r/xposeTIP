import Section from '../shared/Section'

export default function PipelineSection() {
  return (
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
  )
}
