import { Link, Outlet, useLocation } from 'react-router-dom'
import PublicNav from '../landing/PublicNav'
import PublicFooter from '../landing/PublicFooter'

// S301a — Doc hub. Tabs extend in S301b (Engine).
const DOC_TABS = [
  { to: '/doc/architecture', label: 'Architecture' },
  { to: '/doc/bfp', label: 'BFP' },
  { to: '/doc/compare', label: 'Compare' },
  // S301b appends: { to: '/doc/engine', label: 'Engine' }
]

function DocTabBar() {
  const { pathname } = useLocation()
  return (
    <div className="sticky top-16 z-40 border-b border-[#1e1e2e]/50 bg-[#0a0a0f]/80 backdrop-blur-xl">
      <div className="max-w-6xl mx-auto px-6 flex items-center gap-1 overflow-x-auto">
        {DOC_TABS.map((t) => {
          const active = pathname === t.to
          return (
            <Link
              key={t.to}
              to={t.to}
              className={`text-sm px-4 py-3 whitespace-nowrap border-b-2 transition-colors ${
                active
                  ? 'border-[#00ff88] text-[#00ff88]'
                  : 'border-transparent text-gray-400 hover:text-white'
              }`}
            >
              {t.label}
            </Link>
          )
        })}
      </div>
    </div>
  )
}

export default function DocLayout() {
  return (
    <div className="min-h-screen bg-[#0a0a0f] text-white">
      <PublicNav />
      <div className="pt-16">
        <DocTabBar />
        <Outlet />
      </div>
      <PublicFooter />
    </div>
  )
}
