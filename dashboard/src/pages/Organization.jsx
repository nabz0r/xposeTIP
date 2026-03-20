import { useEffect, useState } from 'react'
import { Users, Plus, Trash2, AlertTriangle, Building2 } from 'lucide-react'
import { useAuth } from '../lib/auth'
import { getWorkspaces, createWorkspace, getWorkspaceMembers, inviteMember, updateMemberRole, removeMember, deleteWorkspace } from '../lib/api'

const roleColors = {
  superadmin: '#ff2244', admin: '#ff8800', consultant: '#3388ff', client: '#00ff88', user: '#666688',
}
const roles = ['superadmin', 'admin', 'consultant', 'client', 'user']

export default function Organization() {
  const { user } = useAuth()
  const [workspaces, setWorkspaces] = useState([])
  const [activeWs, setActiveWs] = useState(null)
  const [members, setMembers] = useState([])
  const [showInvite, setShowInvite] = useState(false)
  const [inviteEmail, setInviteEmail] = useState('')
  const [inviteRole, setInviteRole] = useState('user')
  const [showCreate, setShowCreate] = useState(false)
  const [newWsName, setNewWsName] = useState('')
  const [deleteConfirm, setDeleteConfirm] = useState('')
  const [showDelete, setShowDelete] = useState(false)
  const [loading, setLoading] = useState(false)

  useEffect(() => { loadWorkspaces() }, [])

  async function loadWorkspaces() {
    try {
      const data = await getWorkspaces()
      setWorkspaces(data)
      if (data.length > 0 && !activeWs) {
        setActiveWs(data[0])
        loadMembers(data[0].id)
      }
    } catch {}
  }

  async function loadMembers(wsId) {
    try {
      const data = await getWorkspaceMembers(wsId)
      setMembers(data)
    } catch {}
  }

  function selectWorkspace(ws) {
    setActiveWs(ws)
    loadMembers(ws.id)
  }

  async function handleCreate(e) {
    e.preventDefault()
    if (!newWsName) return
    setLoading(true)
    try {
      await createWorkspace({ name: newWsName })
      setShowCreate(false)
      setNewWsName('')
      loadWorkspaces()
    } catch (err) { alert(err.message) }
    finally { setLoading(false) }
  }

  async function handleInvite(e) {
    e.preventDefault()
    if (!inviteEmail || !activeWs) return
    setLoading(true)
    try {
      await inviteMember(activeWs.id, { email: inviteEmail, role: inviteRole })
      setShowInvite(false)
      setInviteEmail('')
      setInviteRole('user')
      loadMembers(activeWs.id)
    } catch (err) { alert(err.message) }
    finally { setLoading(false) }
  }

  async function handleRoleChange(userId, newRole) {
    if (!activeWs) return
    try {
      await updateMemberRole(activeWs.id, userId, { role: newRole })
      loadMembers(activeWs.id)
    } catch (err) { alert(err.message) }
  }

  async function handleRemove(userId) {
    if (!confirm('Remove this member?') || !activeWs) return
    try {
      await removeMember(activeWs.id, userId)
      loadMembers(activeWs.id)
    } catch (err) { alert(err.message) }
  }

  async function handleDeleteWorkspace() {
    if (!activeWs || deleteConfirm !== activeWs.name) return
    try {
      await deleteWorkspace(activeWs.id)
      setShowDelete(false)
      setDeleteConfirm('')
      setActiveWs(null)
      loadWorkspaces()
    } catch (err) { alert(err.message) }
  }

  const currentRole = activeWs?.role
  const isAdmin = currentRole === 'superadmin' || currentRole === 'admin'

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Organization</h1>
        <button onClick={() => setShowCreate(true)}
          className="flex items-center gap-2 bg-[#00ff88] text-black font-semibold rounded-lg px-4 py-2 text-sm hover:bg-[#00ff88]/90">
          <Plus className="w-4 h-4" /> New Workspace
        </button>
      </div>

      {/* Workspace selector */}
      {workspaces.length > 1 && (
        <div className="flex gap-2 overflow-x-auto pb-1">
          {workspaces.map(ws => (
            <button key={ws.id} onClick={() => selectWorkspace(ws)}
              className={`px-4 py-2 rounded-lg text-sm whitespace-nowrap border transition-colors ${
                activeWs?.id === ws.id
                  ? 'border-[#00ff88]/50 bg-[#00ff88]/10 text-[#00ff88]'
                  : 'border-[#1e1e2e] bg-[#12121a] text-gray-400 hover:text-white'
              }`}>
              {ws.name}
            </button>
          ))}
        </div>
      )}

      {activeWs && (
        <>
          {/* Workspace info */}
          <div className="bg-[#12121a] border border-[#1e1e2e] rounded-xl p-5">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-3">
                <Building2 className="w-5 h-5 text-gray-400" />
                <div>
                  <h2 className="text-lg font-semibold">{activeWs.name}</h2>
                  <div className="flex items-center gap-3 text-xs text-gray-500 mt-0.5">
                    <span className="font-mono">{activeWs.slug}</span>
                    <span className="px-1.5 py-0.5 rounded text-[10px] font-medium"
                      style={{ backgroundColor: (roleColors[activeWs.role] || '#666688') + '26', color: roleColors[activeWs.role] }}>
                      {activeWs.role}
                    </span>
                    <span>{activeWs.plan} plan</span>
                  </div>
                </div>
              </div>
              <div className="flex gap-6 text-center">
                <div>
                  <div className="text-2xl font-mono font-bold">{activeWs.member_count}</div>
                  <div className="text-[10px] text-gray-500 uppercase">Members</div>
                </div>
                <div>
                  <div className="text-2xl font-mono font-bold">{activeWs.target_count}</div>
                  <div className="text-[10px] text-gray-500 uppercase">Targets</div>
                </div>
              </div>
            </div>
            {activeWs.created_at && (
              <div className="text-xs text-gray-600">Created {new Date(activeWs.created_at).toLocaleDateString()}</div>
            )}
          </div>

          {/* Members */}
          <div>
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wider flex items-center gap-2">
                <Users className="w-4 h-4" /> Members
              </h3>
              {isAdmin && (
                <button onClick={() => setShowInvite(true)}
                  className="flex items-center gap-1.5 text-sm text-[#00ff88] hover:underline">
                  <Plus className="w-3 h-3" /> Invite
                </button>
              )}
            </div>
            <div className="bg-[#12121a] border border-[#1e1e2e] rounded-xl overflow-hidden">
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-xs text-gray-500 uppercase tracking-wider border-b border-[#1e1e2e]">
                    <th className="text-left px-5 py-3">User</th>
                    <th className="text-left px-5 py-3">Role</th>
                    <th className="text-left px-5 py-3">Joined</th>
                    {isAdmin && <th className="text-left px-5 py-3">Actions</th>}
                  </tr>
                </thead>
                <tbody>
                  {members.map((m, i) => (
                    <tr key={m.user_id} className={`border-t border-[#1e1e2e] ${i % 2 === 1 ? 'bg-white/[0.02]' : ''}`}>
                      <td className="px-5 py-3">
                        <div className="flex items-center gap-3">
                          <div className="w-8 h-8 rounded-full bg-[#1e1e2e] flex items-center justify-center text-xs font-bold text-gray-400">
                            {(m.display_name || m.email)[0].toUpperCase()}
                          </div>
                          <div>
                            <div className="text-sm">{m.display_name || '-'}</div>
                            <div className="text-xs text-gray-500 font-mono">{m.email}</div>
                          </div>
                        </div>
                      </td>
                      <td className="px-5 py-3">
                        {isAdmin && m.user_id !== user?.id ? (
                          <select value={m.role} onChange={e => handleRoleChange(m.user_id, e.target.value)}
                            className="bg-[#0a0a0f] border border-[#1e1e2e] rounded px-2 py-1 text-xs focus:outline-none focus:border-[#00ff88]/50">
                            {roles.map(r => <option key={r} value={r}>{r}</option>)}
                          </select>
                        ) : (
                          <span className="text-xs font-medium px-2 py-0.5 rounded"
                            style={{ backgroundColor: (roleColors[m.role] || '#666688') + '26', color: roleColors[m.role] }}>
                            {m.role}
                          </span>
                        )}
                      </td>
                      <td className="px-5 py-3 text-gray-500 text-xs">
                        {m.joined_at ? new Date(m.joined_at).toLocaleDateString() : '-'}
                      </td>
                      {isAdmin && (
                        <td className="px-5 py-3">
                          {m.user_id !== user?.id && (
                            <button onClick={() => handleRemove(m.user_id)} className="text-gray-500 hover:text-[#ff2244]">
                              <Trash2 className="w-4 h-4" />
                            </button>
                          )}
                        </td>
                      )}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Danger zone */}
          {currentRole === 'superadmin' && (
            <div className="bg-[#12121a] border border-[#ff2244]/30 rounded-xl p-5">
              <div className="flex items-center gap-2 mb-2">
                <AlertTriangle className="w-4 h-4 text-[#ff2244]" />
                <h3 className="text-sm font-semibold text-[#ff2244]">Danger Zone</h3>
              </div>
              <p className="text-xs text-gray-500 mb-4">Deleting this workspace will permanently remove all targets, scans, findings, and members.</p>
              {!showDelete ? (
                <button onClick={() => setShowDelete(true)}
                  className="border border-[#ff2244]/50 text-[#ff2244] rounded-lg px-4 py-2 text-sm hover:bg-[#ff2244]/10">
                  Delete Workspace
                </button>
              ) : (
                <div className="space-y-3">
                  <p className="text-xs text-gray-400">Type <span className="font-mono text-white">{activeWs.name}</span> to confirm:</p>
                  <input type="text" value={deleteConfirm} onChange={e => setDeleteConfirm(e.target.value)}
                    className="w-64 bg-[#0a0a0f] border border-[#ff2244]/30 rounded-lg px-3 py-2 text-sm font-mono focus:outline-none focus:border-[#ff2244]/50" />
                  <div className="flex gap-2">
                    <button onClick={handleDeleteWorkspace} disabled={deleteConfirm !== activeWs.name}
                      className="bg-[#ff2244] text-white font-semibold rounded-lg px-4 py-2 text-sm disabled:opacity-30">
                      Delete Permanently
                    </button>
                    <button onClick={() => { setShowDelete(false); setDeleteConfirm('') }}
                      className="text-sm text-gray-400 hover:text-white px-4 py-2">Cancel</button>
                  </div>
                </div>
              )}
            </div>
          )}
        </>
      )}

      {/* Invite Modal */}
      {showInvite && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50" onClick={() => setShowInvite(false)}>
          <div className="bg-[#12121a] border border-[#1e1e2e] rounded-xl p-6 w-full max-w-md" onClick={e => e.stopPropagation()}>
            <h2 className="text-lg font-semibold mb-4">Invite Member</h2>
            <form onSubmit={handleInvite} className="space-y-4">
              <div>
                <label className="text-xs text-gray-400 mb-1 block">Email</label>
                <input type="email" value={inviteEmail} onChange={e => setInviteEmail(e.target.value)} required
                  className="w-full bg-[#0a0a0f] border border-[#1e1e2e] rounded-lg px-3 py-2 text-sm font-mono focus:outline-none focus:border-[#00ff88]/50" />
              </div>
              <div>
                <label className="text-xs text-gray-400 mb-1 block">Role</label>
                <select value={inviteRole} onChange={e => setInviteRole(e.target.value)}
                  className="w-full bg-[#0a0a0f] border border-[#1e1e2e] rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-[#00ff88]/50">
                  {roles.map(r => <option key={r} value={r}>{r}</option>)}
                </select>
              </div>
              <div className="flex gap-3 justify-end">
                <button type="button" onClick={() => setShowInvite(false)} className="px-4 py-2 text-sm text-gray-400 hover:text-white">Cancel</button>
                <button type="submit" disabled={loading}
                  className="bg-[#00ff88] text-black font-semibold rounded-lg px-6 py-2 text-sm hover:bg-[#00ff88]/90 disabled:opacity-50">
                  {loading ? 'Inviting...' : 'Invite'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Create Workspace Modal */}
      {showCreate && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50" onClick={() => setShowCreate(false)}>
          <div className="bg-[#12121a] border border-[#1e1e2e] rounded-xl p-6 w-full max-w-md" onClick={e => e.stopPropagation()}>
            <h2 className="text-lg font-semibold mb-4">Create Workspace</h2>
            <form onSubmit={handleCreate} className="space-y-4">
              <div>
                <label className="text-xs text-gray-400 mb-1 block">Workspace Name</label>
                <input type="text" value={newWsName} onChange={e => setNewWsName(e.target.value)} required placeholder="e.g. BGL BNP Paribas"
                  className="w-full bg-[#0a0a0f] border border-[#1e1e2e] rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-[#00ff88]/50" />
              </div>
              <div className="flex gap-3 justify-end">
                <button type="button" onClick={() => setShowCreate(false)} className="px-4 py-2 text-sm text-gray-400 hover:text-white">Cancel</button>
                <button type="submit" disabled={loading}
                  className="bg-[#00ff88] text-black font-semibold rounded-lg px-6 py-2 text-sm hover:bg-[#00ff88]/90 disabled:opacity-50">
                  {loading ? 'Creating...' : 'Create'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
