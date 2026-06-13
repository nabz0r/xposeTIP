import { Link, useLocation } from 'react-router-dom'
import { Shield } from 'lucide-react'

// Single source of truth for the top nav across all public pages.
// Active state computed from useLocation() — current page link is accented.
// Page links collapse below md breakpoint; Sign in + Create account stay visible.

const NAV_LINKS = [
  { to: '/welcome', label: 'Product', aliases: ['/'] },
  { to: '/doc', label: 'Doc', aliases: ['/doc/architecture', '/doc/bfp', '/doc/compare', '/doc/engine'] },
  { to: '/manifesto', label: 'Manifesto' },
  { to: '/changelog', label: 'Changelog' },
]

export default function PublicNav() {
  const { pathname } = useLocation()
  const isActive = (link) => pathname === link.to || (link.aliases || []).includes(pathname)

  return (
    <nav className="fixed top-0 left-0 right-0 z-50 border-b border-[#1e1e2e]/50 bg-[#0a0a0f]/80 backdrop-blur-xl">
      <div className="max-w-6xl mx-auto px-6 py-4 flex items-center justify-between">
        <Link to="/welcome" className="flex items-center gap-2">
          <Shield className="w-6 h-6 text-[#00ff88]" />
          <span className="text-xl font-bold tracking-tight font-['Instrument_Sans',sans-serif]">xpose</span>
          <span className="text-[10px] font-mono text-gray-600 ml-1">TIP</span>
        </Link>
        <div className="flex items-center gap-2 md:gap-3">
          {NAV_LINKS.map((link) => (
            <Link
              key={link.to}
              to={link.to}
              className={`hidden md:inline-block text-sm px-3 py-1.5 transition-colors ${
                isActive(link) ? 'text-[#00ff88]' : 'text-gray-400 hover:text-white'
              }`}
            >
              {link.label}
            </Link>
          ))}
          <Link
            to="/login"
            className="text-sm text-gray-400 hover:text-white px-3 py-1.5 transition-colors"
          >
            Sign in
          </Link>
          <Link
            to="/setup"
            className="text-sm bg-[#00ff88] text-black font-semibold rounded-lg px-4 py-1.5 hover:bg-[#00ff88]/90 transition-colors"
          >
            Create account
          </Link>
        </div>
      </div>
    </nav>
  )
}
