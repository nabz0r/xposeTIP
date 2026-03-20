import { useEffect, useState } from 'react'
import { Outlet, NavLink, useNavigate } from 'react-router-dom'
import { LayoutDashboard, Crosshair, Settings, LogOut, Shield, ServerCog, Building2, ChevronDown, Plus } from 'lucide-react'
import { useAuth } from '../lib/auth'
import { getMe, getWorkspaces, switchWorkspace } from '../lib/api'

const navItems = [
  { to: '/', icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/targets', icon: Crosshair, label: 'Targets' },
  { to: '/organization', icon: Building2, label: 'Organization' },
  { to: '/system', icon: ServerCog, label: 'System' },
  { to: '/settings', icon: Settings, label: 'Settings' },
]

const roleColors = {
  superadmin: '#ff2244', admin: '#ff8800', consultant: '#3388ff', client: '#00ff88', user: '#666688',
}

export default function Layout() {
  const { user, setUser, login: authLogin, logout } = useAuth()
  const [workspaces, setWorkspaces] = useState([])
  const [showWsSwitcher, setShowWsSwitcher] = useState(false)
  const navigate = useNavigate()

  useEffect(() => {
    getMe().then(data => {
      setUser(data)
    }).catch(() => {})
    getWorkspaces().then(setWorkspaces).catch(() => {})
  }, [setUser])

  const currentWs = user?.workspaces?.[0]

  async function handleSwitch(wsId) {
    try {
      const data = await switchWorkspace(wsId)
      authLogin(data.access_token, data.refresh_token)
      setShowWsSwitcher(false)
      window.location.reload()
    } catch (err) {
      alert(err.message)
    }
  }

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  return (
    <div className="flex h-screen">
      {/* Sidebar */}
      <aside className="w-60 bg-[#0a0a0f] border-r border-[#1e1e2e] flex flex-col">
        <div className="p-5">
          <div className="flex items-center gap-2">
            <Shield className="w-6 h-6 text-[#00ff88]" />
            <span className="text-xl font-bold text-[#00ff88] font-mono">xpose</span>
          </div>
          {/* Workspace switcher */}
          <div className="relative mt-3">
            <button onClick={() => setShowWsSwitcher(!showWsSwitcher)}
              className="flex items-center justify-between w-full px-3 py-2 rounded-lg bg-[#12121a] border border-[#1e1e2e] text-sm hover:border-[#00ff88]/30 transition-colors">
              <div className="truncate">
                <span className="text-gray-300">{currentWs?.name || 'Workspace'}</span>
              </div>
              <ChevronDown className={`w-3 h-3 text-gray-500 transition-transform ${showWsSwitcher ? 'rotate-180' : ''}`} />
            </button>

            {showWsSwitcher && (
              <div className="absolute left-0 right-0 top-full mt-1 bg-[#12121a] border border-[#1e1e2e] rounded-lg shadow-xl z-50 overflow-hidden">
                {workspaces.map(ws => (
                  <button key={ws.id} onClick={() => handleSwitch(ws.id)}
                    className="w-full px-3 py-2.5 text-left text-sm hover:bg-white/5 flex items-center justify-between">
                    <div>
                      <div className="text-gray-300">{ws.name}</div>
                      <div className="flex items-center gap-2 mt-0.5">
                        <span className="text-[10px] font-medium px-1.5 py-0.5 rounded"
                          style={{ backgroundColor: (roleColors[ws.role] || '#666688') + '26', color: roleColors[ws.role] || '#666688' }}>
                          {ws.role}
                        </span>
                        <span className="text-[10px] text-gray-600">{ws.target_count} targets</span>
                      </div>
                    </div>
                  </button>
                ))}
                <button onClick={() => { setShowWsSwitcher(false); navigate('/organization') }}
                  className="w-full px-3 py-2.5 text-left text-xs text-[#00ff88] hover:bg-white/5 flex items-center gap-2 border-t border-[#1e1e2e]">
                  <Plus className="w-3 h-3" /> Create workspace
                </button>
              </div>
            )}
          </div>
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
