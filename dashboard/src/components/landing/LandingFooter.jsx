import { Shield } from 'lucide-react'

export default function LandingFooter() {
  return (
    <footer className="border-t border-[#1e1e2e] py-12">
      <div className="max-w-5xl mx-auto px-6">
        <div className="flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <Shield className="w-5 h-5 text-[#00ff88]" />
            <span className="font-bold font-['Instrument_Sans',sans-serif]">xpose</span>
            <span className="text-[10px] font-mono text-gray-600">TIP</span>
            <span className="text-xs text-gray-600 font-mono ml-2">v0.80.0</span>
          </div>
          <p className="text-xs text-gray-600 font-mono text-center">
            Threat Identity Platform · From IOCs to identities · Open Source
          </p>
          <div className="flex items-center gap-4 text-xs text-gray-500">
            <a href="/architecture" className="hover:text-white transition-colors">Architecture</a>
            <a href="/architecture#roadmap" className="hover:text-white transition-colors">Roadmap</a>
            <a href="https://github.com/nabz0r/xposeTIP" className="hover:text-white transition-colors">GitHub</a>
            <a href="/manifesto" className="hover:text-white transition-colors">Manifesto</a>
            <a href="/login" className="hover:text-white transition-colors">Sign in</a>
          </div>
        </div>
      </div>
    </footer>
  )
}
