import { Link } from 'react-router-dom'
import { Shield } from 'lucide-react'

// Single source of truth for the bottom footer across all public pages.
// Same link set as PublicNav (no Create account CTA) + GitHub (external).
// Pages that need editorial closing content (e.g. Manifesto) render it
// ABOVE this footer; PublicFooter itself stays identical everywhere.

const FOOTER_LINKS = [
  { to: '/welcome', label: 'Product' },
  { to: '/architecture', label: 'Architecture' },
  { to: '/compare', label: 'Compare' },
  { to: '/manifesto', label: 'Manifesto' },
  { to: '/changelog', label: 'Changelog' },
]

export default function PublicFooter() {
  return (
    <footer className="border-t border-[#1e1e2e] py-12">
      <div className="max-w-5xl mx-auto px-6">
        <div className="flex flex-col md:flex-row items-center justify-between gap-4">
          <Link to="/welcome" className="flex items-center gap-2">
            <Shield className="w-5 h-5 text-[#00ff88]" />
            <span className="font-bold font-['Instrument_Sans',sans-serif]">xpose</span>
            <span className="text-[10px] font-mono text-gray-600">TIP</span>
            <span className="text-xs text-gray-600 font-mono ml-2">v1.6.2</span>
          </Link>
          <p className="text-xs text-gray-600 font-mono text-center">
            Identity Threat Intelligence · Built in Luxembourg 🇱🇺
          </p>
          <div className="flex flex-wrap items-center justify-center gap-x-4 gap-y-2 text-xs text-gray-500">
            {FOOTER_LINKS.map((link) => (
              <Link key={link.to} to={link.to} className="hover:text-white transition-colors">
                {link.label}
              </Link>
            ))}
            <a
              href="https://github.com/nabz0r/xposeTIP"
              target="_blank"
              rel="noopener noreferrer"
              className="hover:text-white transition-colors"
            >
              GitHub
            </a>
            <Link to="/login" className="hover:text-white transition-colors">
              Sign in
            </Link>
          </div>
        </div>
      </div>
    </footer>
  )
}
