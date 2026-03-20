import { useEffect } from 'react'
import { Outlet, NavLink, useNavigate } from 'react-router-dom'
import { LayoutDashboard, Crosshair, Settings, LogOut, Shield, ServerCog } from 'lucide-react'
import { useAuth } from '../lib/auth'
import { getMe } from '../lib/api'

const navItems = [
  { to: '/', icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/targets', icon: Crosshair, label: 'Targets' },
  { to: '/system', icon: ServerCog, label: 'System' },
  { to: '/settings', icon: Settings, label: 'Settings' },
]

export default function Layout() {
  const { user, setUser, logout } = useAuth()
  const navigate = useNavigate()

  useEffect(() => {
    getMe().then(setUser).catch(() => {})
  }, [setUser])

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  return (
    <div className="flex h-screen">
      {/* Sidebar */}
      <aside className="w-60 bg-[#0a0a0f] border-r border-[#1e1e2e] flex flex-col">
        <div className="p-5 flex items-center gap-2">
          <Shield className="w-6 h-6 text-[#00ff88]" />
          <span className="text-xl font-bold text-[#00ff88] font-mono">xpose</span>
        </div>
        <nav className="flex-1 px-3 space-y-1">
          {navItems.map(({ to, icon: Icon, label }) => (
            <NavLink
              key={to}
              to={to}
              end={to === '/'}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-colors ${
                  isActive
                    ? 'bg-[#00ff88]/10 text-[#00ff88]'
                    : 'text-gray-400 hover:text-white hover:bg-white/5'
                }`
              }
            >
              <Icon className="w-4 h-4" />
              {label}
            </NavLink>
          ))}
        </nav>
        <div className="p-3 border-t border-[#1e1e2e]">
          <div className="px-3 py-2 text-xs text-gray-500 truncate">
            {user?.email || '...'}
          </div>
          <button
            onClick={handleLogout}
            className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm text-gray-400 hover:text-white hover:bg-white/5 w-full"
          >
            <LogOut className="w-4 h-4" />
            Logout
          </button>
        </div>
      </aside>

      {/* Main content */}
      <main className="flex-1 bg-[#0f0f14] overflow-auto">
        <div className="p-6">
          <Outlet />
        </div>
      </main>
    </div>
  )
}
