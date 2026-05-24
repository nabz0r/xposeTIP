import { useEffect, useState } from 'react'
import { Outlet, NavLink, useNavigate, useLocation, useSearchParams } from 'react-router-dom'
import { LayoutDashboard, Crosshair, Settings, LogOut, Shield, ServerCog, Building2, ChevronDown, Plus, Menu, X, Globe, Briefcase, Layers } from 'lucide-react'
import { useAuth } from '../lib/auth'
import { getMe, getWorkspaces, switchWorkspace } from '../lib/api'
import { planColor } from '../lib/planColors'

const navItems = [
  { to: '/', icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/targets', icon: Crosshair, label: 'Targets' },
  { to: '/scrapers', icon: Globe, label: 'Scrapers' },
  { to: '/organization', icon: Building2, label: 'Organization' },
  { to: '/consulting', icon: Briefcase, label: 'Consulting', roles: ['superadmin', 'admin', 'consultant'] },
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
  '/consulting': 'Consulting',
  '/system': 'System',
  '/settings': 'Settings',
}

export default function Layout() {
  const { user, setUser, login: authLogin, logout, refreshKey, triggerRefresh } = useAuth()
  const [workspaces, setWorkspaces] = useState([])
  const [showWsSwitcher, setShowWsSwitcher] = useState(false)
  const [collapsed, setCollapsed] = useState(false)
  const [mobileOpen, setMobileOpen] = useState(false)
  const navigate = useNavigate()
  const location = useLocation()
  const [searchParams] = useSearchParams()
  const isAllMode = location.pathname.startsWith('/targets') && searchParams.get('all') === '1'

  useEffect(() => {
    getMe().then(data => {
      setUser(data)
    }).catch(() => {})
    getWorkspaces().then(setWorkspaces).catch(() => {})
  }, [setUser, refreshKey])

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
      triggerRefresh()
      navigate('/')
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
                {currentWs?.plan && (
                  <span className="ml-1.5 text-[9px] font-mono font-bold px-1.5 py-0.5 rounded-full"
                    style={{ backgroundColor: planColor(currentWs.plan) + '26', color: planColor(currentWs.plan) }}>
                    {currentWs.plan}
                  </span>
                )}
              </div>
              <ChevronDown className={`w-3 h-3 text-gray-500 transition-transform ${showWsSwitcher ? 'rotate-180' : ''}`} />
            </button>

            {showWsSwitcher && (
              <div className="absolute left-0 right-0 top-full mt-1 bg-[#12121a] border border-[#1e1e2e] rounded-lg shadow-xl z-50 overflow-hidden">
                {(currentWs?.role === 'superadmin' || currentWs?.role === 'admin') && (
                  <button onClick={() => { setShowWsSwitcher(false); navigate('/targets?all=1') }}
                    className="w-full px-3 py-2.5 text-left text-sm hover:bg-white/5 flex items-center gap-2 border-b border-[#1e1e2e]">
                    <Layers className="w-4 h-4 text-[#00ff88] shrink-0" />
                    <div>
                      <div className="text-gray-300">All workspaces</div>
                      <div className="text-[10px] text-gray-600 mt-0.5">admin view — all targets across workspaces</div>
                    </div>
                  </button>
                )}
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
                        {ws.plan && (
                          <span className="text-[9px] font-mono px-1 py-0.5 rounded"
                            style={{ backgroundColor: planColor(ws.plan) + '1a', color: planColor(ws.plan) }}>
                            {ws.plan}
                          </span>
                        )}
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

      {/* S192 Bug 11: ALL workspaces mode banner — Targets-only by design (S188).
          Other nav items are disabled in this mode to signal scope; clicking them
          would otherwise bounce back to the JWT workspace context which is confusing. */}
      {isAllMode && !collapsed && (
        <div className="mx-3 mb-2 px-3 py-2 bg-[#00ff88]/10 border border-[#00ff88]/30 rounded-lg flex items-center gap-2">
          <Layers className="w-3.5 h-3.5 text-[#00ff88] shrink-0" />
          <div className="flex-1">
            <div className="text-[11px] font-mono text-[#00ff88] uppercase tracking-wider">All workspaces</div>
            <div className="text-[10px] text-gray-500 mt-0.5">Targets view only</div>
          </div>
        </div>
      )}

      <nav className="flex-1 px-3 space-y-1">
        {navItems
          .filter(item => !item.roles || item.roles.includes(currentWs?.role))
          .map(({ to, icon: Icon, label }) => {
            // S192 Bug 11: in ALL mode, disable nav items other than Targets
            // (which is the only tab that respects ?all=1). Clicking would
            // otherwise reset the user to their JWT workspace context.
            const isDisabledInAllMode = isAllMode && to !== '/targets'
            if (isDisabledInAllMode) {
              return (
                <div
                  key={to}
                  title={collapsed ? `${label} (disabled in ALL mode)` : 'Disabled in ALL workspaces mode'}
                  className={`flex items-center gap-3 ${collapsed ? 'justify-center' : ''} px-3 py-2.5 rounded-lg text-sm text-gray-600 opacity-50 cursor-not-allowed select-none`}
                >
                  <Icon className="w-4 h-4 shrink-0" />
                  {!collapsed && label}
                </div>
              )
            }
            return (
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
            )
          })}
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
          <Outlet context={{ currentWs }} />
        </div>
      </main>
    </div>
  )
}
