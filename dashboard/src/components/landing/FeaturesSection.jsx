import Section from '../shared/Section'
import { EXPOSURES } from './constants'

export default function FeaturesSection() {
  return (
    <Section className="py-32">
      <div className="max-w-4xl mx-auto px-6">
        <h2 className="text-3xl md:text-4xl font-bold text-center mb-16 font-['Instrument_Sans',sans-serif]">
          What we uncover
        </h2>

        <div className="grid md:grid-cols-2 gap-8">
          {EXPOSURES.map(({ icon: Icon, title, desc }) => (
            <div key={title} className="flex gap-4">
              <div className="w-10 h-10 rounded-lg bg-[#1e1e2e] flex items-center justify-center shrink-0">
                <Icon className="w-5 h-5 text-gray-400" />
              </div>
              <div>
                <h3 className="text-sm font-semibold mb-1">{title}</h3>
                <p className="text-sm text-gray-500 leading-relaxed">{desc}</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </Section>
  )
}
