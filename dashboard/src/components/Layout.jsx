import { useEffect, useState } from 'react'
import { Outlet, NavLink, useNavigate, useLocation } from 'react-router-dom'
import { LayoutDashboard, Crosshair, Settings, LogOut, Shield, ServerCog, Building2, ChevronDown, Plus, Menu, X, Globe } from 'lucide-react'
import { useAuth } from '../lib/auth'
import { getMe, getWorkspaces, switchWorkspace } from '../lib/api'

const navItems = [
  { to: '/', icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/targets', icon: Crosshair, label: 'Targets' },
  { to: '/scrapers', icon: Globe, label: 'Scrapers' },
  { to: '/organization', icon: Building2, label: 'Organization' },
  { to: '/system', icon: ServerCog, label: 'System' },
  { to: '/settings', icon: Settings, label: 'Settings' },
]

const roleColors = {
  superadmin: '#ff2244', admin: '#ff8800', consultant: '#3388ff', client: '#00ff88', user: '#666688',
}

// Dynamic page titles
const pageTitles = {
  '/': 'Dashboard',
  '/targets': 'Targets',
  '/scrapers': 'Scrapers',
  '/organization': 'Organization',
  '/system': 'System',
  '/settings': 'Settings',
}

export default function Layout() {
  const { user, setUser, login: authLogin, logout } = useAuth()
  const [workspaces, setWorkspaces] = useState([])
  const [showWsSwitcher, setShowWsSwitcher] = useState(false)
  const [collapsed, setCollapsed] = useState(false)
  const [mobileOpen, setMobileOpen] = useState(false)
  const navigate = useNavigate()
  const location = useLocation()

  useEffect(() => {
    getMe().then(data => {
      setUser(data)
    }).catch(() => {})
    getWorkspaces().then(setWorkspaces).catch(() => {})
  }, [setUser])

  // Dynamic page title
  useEffect(() => {
    const base = 'xpose'
    const path = location.pathname
    const match = Object.entries(pageTitles).find(([p]) => path === p)
    if (match) {
      document.title = `${match[1]} — ${base}`
    } else if (path.startsWith('/targets/')) {
      document.title = `Target Detail — ${base}`
    } else {
      document.title = base
    }
  }, [location.pathname])

  // Auto-collapse on small screens
  useEffect(() => {
    const check = () => setCollapsed(window.innerWidth < 1024)
    check()
    window.addEventListener('resize', check)
    return () => window.removeEventListener('resize', check)
  }, [])

  // Close mobile nav on route change
  useEffect(() => { setMobileOpen(false) }, [location.pathname])

  // Identify current workspace from JWT token's workspace_id
  const currentWsId = (() => {
    const token = localStorage.getItem('xpose_token')
    if (!token) return null
    try {
      const payload = JSON.parse(atob(token.split('.')[1]))
      return payload.workspace_id
    } catch { return null }
  })()
  const currentWs = workspaces.find(ws => ws.id === currentWsId) || user?.workspaces?.[0]

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

  const sidebarContent = (
    <>
      <div className={collapsed ? 'p-3' : 'p-5'}>
        <div className="flex items-center gap-2">
          <Shield className="w-6 h-6 text-[#00ff88] shrink-0" />
          {!collapsed && <span className="text-xl font-bold text-[#00ff88] font-mono">xpose</span>}
        </div>
        {/* Workspace switcher */}
        {!collapsed && (
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
        )}
      </div>

      <nav className="flex-1 px-3 space-y-1">
        {navItems.map(({ to, icon: Icon, label }) => (
          <NavLink
            key={to}
            to={to}
            end={to === '/'}
            title={collapsed ? label : undefined}
            className={({ isActive }) =>
              `flex items-center gap-3 ${collapsed ? 'justify-center' : ''} px-3 py-2.5 rounded-lg text-sm transition-colors ${
                isActive
                  ? 'bg-[#00ff88]/10 text-[#00ff88]'
                  : 'text-gray-400 hover:text-white hover:bg-white/5'
              }`
            }
          >
            <Icon className="w-4 h-4 shrink-0" />
            {!collapsed && label}
          </NavLink>
        ))}
      </nav>
      <div className="p-3 border-t border-[#1e1e2e]">
        {!collapsed && (
          <div className="px-3 py-2 text-xs text-gray-500 truncate">
            {user?.email || '...'}
          </div>
        )}
        <button
          onClick={handleLogout}
          title={collapsed ? 'Logout' : undefined}
          className={`flex items-center gap-3 ${collapsed ? 'justify-center' : ''} px-3 py-2.5 rounded-lg text-sm text-gray-400 hover:text-white hover:bg-white/5 w-full`}
        >
          <LogOut className="w-4 h-4 shrink-0" />
          {!collapsed && 'Logout'}
        </button>
      </div>
    </>
  )

  return (
    <div className="flex h-screen">
      {/* Mobile menu button */}
      <button onClick={() => setMobileOpen(!mobileOpen)}
        className="lg:hidden fixed top-4 left-4 z-50 p-2 rounded-lg bg-[#12121a] border border-[#1e1e2e] text-gray-400 hover:text-white">
        {mobileOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
      </button>

      {/* Mobile overlay */}
      {mobileOpen && (
        <div className="lg:hidden fixed inset-0 bg-black/60 z-40" onClick={() => setMobileOpen(false)} />
      )}

      {/* Sidebar */}
      <aside className={`
        ${collapsed ? 'w-16' : 'w-60'} bg-[#0a0a0f] border-r border-[#1e1e2e] flex flex-col shrink-0 transition-all duration-200
        max-lg:fixed max-lg:inset-y-0 max-lg:left-0 max-lg:z-50 max-lg:w-60
        ${mobileOpen ? 'max-lg:translate-x-0' : 'max-lg:-translate-x-full'}
      `}>
        {sidebarContent}
      </aside>

      {/* Main content */}
      <main className="flex-1 bg-[#0f0f14] overflow-auto">
        <div key={location.pathname} className="p-6 max-lg:pt-16 animate-page-in">
          <Outlet />
        </div>
      </main>
    </div>
  )
}
