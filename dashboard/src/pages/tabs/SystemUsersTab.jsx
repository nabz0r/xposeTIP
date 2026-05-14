import React, { useEffect, useState } from 'react'
import { Search, ChevronDown, ChevronRight } from 'lucide-react'
import { adminListUsers, adminUpdateUser } from '../../lib/api'
import { planColors } from '../../lib/planColors'

const roleColors = {
  superadmin: '#ff2244', admin: '#ff8800', consultant: '#3388ff', client: '#00ff88', user: '#666688',
}

export default function SystemUsersTab() {
  const [users, setUsers] = useState([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [expanded, setExpanded] = useState(null)

  useEffect(() => { loadUsers() }, [])

  async function loadUsers() {
    try {
      const data = await adminListUsers()
      setUsers(data.items || [])
    } catch {}
    finally { setLoading(false) }
  }

  async function toggleActive(userId, currentActive) {
    try {
      await adminUpdateUser(userId, { is_active: !currentActive })
      loadUsers()
    } catch (err) { alert(err.message) }
  }

  if (loading) return <div className="text-gray-500 py-8 text-center">Loading users...</div>

  const filtered = users.filter(u =>
    !search || u.email.toLowerCase().includes(search.toLowerCase()) || (u.display_name || '').toLowerCase().includes(search.toLowerCase())
  )

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <span className="text-xs text-gray-500 uppercase tracking-wider font-semibold">Platform Users ({users.length})</span>
      </div>

      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
        <input type="text" value={search} onChange={e => setSearch(e.target.value)} placeholder="Search by email or name..."
          className="w-full bg-[#12121a] border border-[#1e1e2e] rounded-lg pl-10 pr-3 py-2 text-sm font-mono focus:outline-none focus:border-[#00ff88]/50" />
      </div>

      <div className="bg-[#12121a] border border-[#1e1e2e] rounded-xl overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-xs text-gray-500 uppercase tracking-wider border-b border-[#1e1e2e]">
              <th className="text-left px-5 py-3 w-8"></th>
              <th className="text-left px-5 py-3">Email</th>
              <th className="text-left px-5 py-3">Display Name</th>
              <th className="text-left px-5 py-3">Role</th>
              <th className="text-left px-5 py-3">Workspaces</th>
              <th className="text-left px-5 py-3">Last Login</th>
              <th className="text-left px-5 py-3">Status</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map((u, i) => {
              const isExpanded = expanded === u.id
              return (
                <React.Fragment key={u.id}>
                  <tr
                    onClick={() => setExpanded(isExpanded ? null : u.id)}
                    className={`border-t border-[#1e1e2e] cursor-pointer hover:bg-white/[0.03] ${i % 2 === 1 ? 'bg-white/[0.02]' : ''}`}
                  >
                    <td className="px-5 py-3 text-gray-500">
                      {isExpanded ? <ChevronDown className="w-3 h-3" /> : <ChevronRight className="w-3 h-3" />}
                    </td>
                    <td className="px-5 py-3 font-mono">{u.email}</td>
                    <td className="px-5 py-3 text-gray-400">{u.display_name || '-'}</td>
                    <td className="px-5 py-3">
                      <span className="text-xs font-medium px-2 py-0.5 rounded"
                        style={{ backgroundColor: (roleColors[u.highest_role] || '#666688') + '26', color: roleColors[u.highest_role] || '#666688' }}>
                        {u.highest_role}
                      </span>
                    </td>
                    <td className="px-5 py-3 font-mono text-gray-400">{u.workspace_count}</td>
                    <td className="px-5 py-3 text-xs text-gray-500">
                      {u.last_login ? new Date(u.last_login).toLocaleString() : 'Never'}
                    </td>
                    <td className="px-5 py-3">
                      <button onClick={(e) => { e.stopPropagation(); toggleActive(u.id, u.is_active) }}
                        className={`text-[10px] px-2 py-0.5 rounded-full font-medium ${
                          u.is_active ? 'bg-[#00ff88]/15 text-[#00ff88]' : 'bg-[#ff2244]/15 text-[#ff2244]'
                        }`}>
                        {u.is_active ? 'active' : 'inactive'}
                      </button>
                    </td>
                  </tr>
                  {isExpanded && (
                    <tr className="border-t border-[#1e1e2e]/50">
                      <td colSpan={7} className="px-10 py-3 bg-[#0a0a0f]">
                        <div className="text-xs text-gray-500 mb-2">Workspace memberships</div>
                        <div className="space-y-1.5">
                          {u.workspaces.map(ws => (
                            <div key={ws.workspace_id} className="flex items-center gap-3 text-xs">
                              <span className="text-gray-300">{ws.workspace_name}</span>
                              <span className="font-medium px-1.5 py-0.5 rounded text-[10px]"
                                style={{ backgroundColor: (roleColors[ws.role] || '#666688') + '26', color: roleColors[ws.role] || '#666688' }}>
                                {ws.role}
                              </span>
                              <span className="font-mono px-1.5 py-0.5 rounded text-[10px]"
                                style={{ backgroundColor: (planColors[ws.plan] || '#666688') + '15', color: planColors[ws.plan] || '#666688' }}>
                                {ws.plan}
                              </span>
                            </div>
                          ))}
                          {u.workspaces.length === 0 && <span className="text-gray-600">No workspaces</span>}
                        </div>
                        <div className="mt-2 text-[10px] text-gray-600">
                          Created: {u.created_at ? new Date(u.created_at).toLocaleString() : '-'}
                        </div>
                      </td>
                    </tr>
                  )}
                </React.Fragment>
              )
            })}
            {filtered.length === 0 && (
              <tr><td colSpan={7} className="px-5 py-8 text-center text-gray-500">No users found</td></tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}
