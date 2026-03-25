import Section from '../shared/Section'
import LiveCounter from './LiveCounter'

export default function ProblemSection() {
  return (
    <Section className="py-32">
      <div className="max-w-5xl mx-auto px-6">
        <h2 className="text-3xl md:text-4xl font-bold text-center mb-16 font-['Instrument_Sans',sans-serif]">
          Two approaches to threat intelligence
        </h2>

        <div className="grid md:grid-cols-2 gap-8 md:gap-12">
          {/* Left — Traditional TI */}
          <div className="bg-[#12121a] border border-[#ff2244]/20 rounded-xl p-8">
            <div className="text-xs font-mono text-[#ff2244] mb-6 uppercase tracking-wider">Traditional TI</div>
            <div className="space-y-5">
              {[
                { value: '100K+', label: 'IOCs ingested per day' },
                { value: '95%', label: 'noise — stale, duplicated, irrelevant' },
                { value: '24h', label: 'average IP indicator lifespan' },
                { value: '0', label: 'human context behind the indicator' },
                { value: '∞', label: 'alert fatigue' },
              ].map(item => (
                <div key={item.label} className="flex items-baseline gap-3">
                  <span className="text-xl font-mono font-bold text-[#ff2244]/70 w-16 shrink-0 text-right">{item.value}</span>
                  <span className="text-sm text-gray-500">{item.label}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Right — xposeTIP */}
          <div className="bg-[#12121a] border border-[#00ff88]/20 rounded-xl p-8">
            <div className="text-xs font-mono text-[#00ff88] mb-6 uppercase tracking-wider">xposeTIP</div>
            <div className="space-y-5">
              {[
                { value: '1', label: 'email = 1 complete persona' },
                { value: '9', label: 'behavioral dimensions — unique as DNA' },
                { value: '∞', label: 'fingerprint persists when IP changes' },
                { value: '1', label: 'human behind every indicator' },
                { value: '3', label: 'concrete actions — not alerts' },
              ].map(item => (
                <div key={item.label} className="flex items-baseline gap-3">
                  <span className="text-xl font-mono font-bold text-[#00ff88]/70 w-16 shrink-0 text-right">{item.value}</span>
                  <span className="text-sm text-gray-400">{item.label}</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Breach counter below */}
        <div className="mt-20 text-center">
          <LiveCounter />
          <p className="text-sm text-gray-600 mt-4 max-w-md mx-auto">
            Every leaked record is a data point. Traditional TI counts them. xposeTIP connects them to a person.
          </p>
        </div>
      </div>
    </Section>
  )
}
