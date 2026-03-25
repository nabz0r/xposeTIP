import { Link } from 'react-router-dom'
import { Shield } from 'lucide-react'
import Section from '../shared/Section'

export function ArchCTA() {
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

export function ArchFooter() {
  return (
    <footer className="border-t border-[#1e1e2e] py-8">
      <div className="max-w-5xl mx-auto px-6 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Shield className="w-4 h-4 text-[#00ff88]" />
          <span className="font-bold text-sm font-['Instrument_Sans',sans-serif]">xpose</span>
          <span className="text-[10px] font-mono text-gray-600">TIP</span>
          <span className="text-xs text-gray-600 font-mono ml-2">v0.73.0</span>
        </div>
        <div className="flex items-center gap-4 text-xs text-gray-500">
          <Link to="/welcome" className="hover:text-white transition-colors">Home</Link>
          <a href="https://github.com/nabz0r/xposeTIP" className="hover:text-white transition-colors">GitHub</a>
        </div>
      </div>
    </footer>
  )
}
