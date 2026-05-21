import { Link } from 'react-router-dom'
import Section from '../shared/Section'

export default function ArchCTA() {
  return (
    <Section className="py-20">
      <div className="max-w-3xl mx-auto px-6 text-center">
        <h2 className="text-2xl font-bold mb-3 font-['Instrument_Sans',sans-serif]">
          From IOCs to identities
        </h2>
        <p className="text-gray-500 mb-6">The future of threat intelligence starts here. Free scan, no signup.</p>
        <Link
          to="/welcome"
          className="inline-flex items-center gap-2 bg-[#00ff88] text-black font-semibold rounded-lg px-6 py-3 text-sm hover:bg-[#00ff88]/90 transition-colors"
        >
          Try it now
        </Link>
      </div>
    </Section>
  )
}
