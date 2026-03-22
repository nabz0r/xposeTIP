import React, { useState } from 'react'
import { LayoutDashboard, HeartPulse, Puzzle, ScrollText, Users, Building2, ShieldBan } from 'lucide-react'
import { useAuth } from '../lib/auth'
import LogViewer from '../components/LogViewer'
import SystemDashboardTab from './tabs/SystemDashboardTab'
import SystemHealthTab from './tabs/SystemHealthTab'
import SystemModulesTab from './tabs/SystemModulesTab'
import SystemUsersTab from './tabs/SystemUsersTab'
import SystemWorkspacesTab from './tabs/SystemWorkspacesTab'
import SystemNameRulesTab from './tabs/SystemNameRulesTab'

export default function System() {
  const [activeTab, setActiveTab] = useState('dashboard')
  const { user } = useAuth()

  // Check if superadmin from JWT
  const isSuperAdmin = (() => {
    const token = localStorage.getItem('xpose_token')
    if (!token) return false
    try {
      return JSON.parse(atob(token.split('.')[1])).role === 'superadmin'
    } catch { return false }
  })()

  const TABS = [
    { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { id: 'health', label: 'Health', icon: HeartPulse },
    { id: 'modules', label: 'Modules', icon: Puzzle },
    { id: 'logs', label: 'Logs', icon: ScrollText },
    ...(isSuperAdmin ? [
      { id: 'users', label: 'Users', icon: Users },
      { id: 'workspaces', label: 'Workspaces', icon: Building2 },
      { id: 'namerules', label: 'Name Rules', icon: ShieldBan },
    ] : []),
  ]

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">System</h1>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 border-b border-[#1e1e2e]">
        {TABS.map(tab => {
          const Icon = tab.icon
          const active = activeTab === tab.id
          return (
            <button key={tab.id} onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-2 px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
                active
                  ? 'border-[#00ff88] text-[#00ff88]'
                  : 'border-transparent text-gray-500 hover:text-gray-300'
              }`}>
              <Icon className="w-4 h-4" />
              {tab.label}
            </button>
          )
        })}
      </div>

      {/* Tab content */}
      {activeTab === 'dashboard' && <SystemDashboardTab />}
      {activeTab === 'health' && <SystemHealthTab />}
      {activeTab === 'modules' && <SystemModulesTab />}
      {activeTab === 'logs' && <LogViewer />}
      {activeTab === 'users' && isSuperAdmin && <SystemUsersTab />}
      {activeTab === 'workspaces' && isSuperAdmin && <SystemWorkspacesTab />}
      {activeTab === 'namerules' && isSuperAdmin && <SystemNameRulesTab />}
    </div>
  )
}
