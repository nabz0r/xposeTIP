import { useEffect, useState } from 'react'
import { Users, Plus, Trash2, AlertTriangle, Building2, CheckCircle, XCircle, CreditCard } from 'lucide-react'
import { useAuth } from '../lib/auth'
import { getWorkspaces, createWorkspace, getWorkspaceMembers, inviteMember, updateMemberRole, removeMember, deleteWorkspace, updateWorkspacePlan, getWorkspaceUsage, getPlans } from '../lib/api'
import { planColor } from '../lib/planColors'

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
  const [usage, setUsage] = useState(null)
  const [plans, setPlans] = useState(null)
  const [upgrading, setUpgrading] = useState(false)

  // Check if superadmin from JWT
  const isSuperAdmin = (() => {
    const token = localStorage.getItem('xpose_token')
    if (!token) return false
    try {
      return JSON.parse(atob(token.split('.')[1])).role === 'superadmin'
    } catch { return false }
  })()

  useEffect(() => { loadWorkspaces(); getPlans().then(setPlans).catch(() => {}) }, [])

  async function loadWorkspaces() {
    try {
      const data = await getWorkspaces()
      setWorkspaces(data)
      if (data.length > 0 && !activeWs) {
        setActiveWs(data[0])
        loadMembers(data[0].id)
        loadUsage(data[0].id)
      }
    } catch {}
  }

  async function loadMembers(wsId) {
    try {
      const data = await getWorkspaceMembers(wsId)
      setMembers(data)
    } catch {}
  }

  async function loadUsage(wsId) {
    try {
      const data = await getWorkspaceUsage(wsId)
      setUsage(data)
    } catch { setUsage(null) }
  }

  function selectWorkspace(ws) {
    setActiveWs(ws)
    loadMembers(ws.id)
    loadUsage(ws.id)
  }

  async function handlePlanChange(newPlan) {
    if (!activeWs) return
    try {
      await updateWorkspacePlan(activeWs.id, newPlan)
      loadWorkspaces()
      loadUsage(activeWs.id)
    } catch (err) { alert(err.message) }
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
              className={`px-4 py-2 rounded-lg text-sm whitespace-nowrap border transition-colors flex items-center gap-1.5 ${
                activeWs?.id === ws.id
                  ? 'border-[#00ff88]/50 bg-[#00ff88]/10 text-[#00ff88]'
                  : 'border-[#1e1e2e] bg-[#12121a] text-gray-400 hover:text-white'
              }`}>
              {ws.name}
              {ws.plan && (
                <span className="text-[9px] font-mono font-bold px-1.5 py-0.5 rounded-full uppercase"
                  style={{ backgroundColor: planColor(ws.plan) + '26', color: planColor(ws.plan) }}>
                  {ws.plan}
                </span>
              )}
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
                    {isSuperAdmin ? (
                      <select value={activeWs.plan} onChange={e => handlePlanChange(e.target.value)}
                        className="bg-[#0a0a0f] border border-[#1e1e2e] rounded px-2 py-0.5 text-xs focus:outline-none focus:border-[#00ff88]/50">
                        <option value="free">free</option>
                        <option value="consultant">consultant</option>
                        <option value="enterprise">enterprise</option>
                      </select>
                    ) : (
                      <span>{activeWs.plan} plan</span>
                    )}
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
            {/* Usage bar */}
            {usage && usage.limits.max_targets !== -1 && (
              <div className="mt-3 space-y-2">
                <div className="space-y-1">
                  <div className="flex justify-between text-xs">
                    <span className="text-gray-500">Targets</span>
                    <span className="font-mono text-gray-300">{usage.usage.targets} / {usage.limits.max_targets}</span>
                  </div>
                  <div className="h-1.5 bg-[#0a0a0f] rounded-full overflow-hidden">
                    <div className="h-full rounded-full bg-[#00ff88] transition-all"
                      style={{ width: `${Math.min(100, (usage.usage.targets / usage.limits.max_targets) * 100)}%` }} />
                  </div>
                </div>
                <div className="space-y-1">
                  <div className="flex justify-between text-xs">
                    <span className="text-gray-500">Scans this month</span>
                    <span className="font-mono text-gray-300">{usage.usage.scans_this_month} / {usage.limits.max_scans_per_month === -1 ? '∞' : usage.limits.max_scans_per_month}</span>
                  </div>
                  {usage.limits.max_scans_per_month !== -1 && (
                    <div className="h-1.5 bg-[#0a0a0f] rounded-full overflow-hidden">
                      <div className="h-full rounded-full bg-[#3388ff] transition-all"
                        style={{ width: `${Math.min(100, (usage.usage.scans_this_month / usage.limits.max_scans_per_month) * 100)}%` }} />
                    </div>
                  )}
                </div>
              </div>
            )}
            {activeWs.created_at && (
              <div className="text-xs text-gray-600 mt-2">Created {new Date(activeWs.created_at).toLocaleDateString()}</div>
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
                    <th className="text-left px-5 py-3">Status</th>
                    <th className="text-left px-5 py-3">Joined</th>
                    <th className="text-left px-5 py-3">Last Login</th>
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
                      <td className="px-5 py-3">
                        {m.last_login ? (
                          <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-[#00ff88]/15 text-[#00ff88]">active</span>
                        ) : (
                          <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-[#666688]/15 text-[#666688]">invited</span>
                        )}
                      </td>
                      <td className="px-5 py-3 text-gray-500 text-xs font-mono">
                        {m.joined_at ? new Date(m.joined_at).toLocaleDateString() : '-'}
                      </td>
                      <td className="px-5 py-3 text-gray-500 text-xs font-mono">
                        {m.last_login ? new Date(m.last_login).toLocaleDateString() : 'Never'}
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

          {/* Plan & Billing */}
          {usage && plans && (
            <div>
              <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wider flex items-center gap-2 mb-3">
                <CreditCard className="w-4 h-4" /> Plan & Billing
              </h3>
              <div className="bg-[#12121a] border border-[#1e1e2e] rounded-xl p-5 space-y-4">
                {/* Current plan + usage */}
                <div className="flex items-center gap-3">
                  <h4 className="text-sm font-semibold">Current Plan</h4>
                  <span className="text-xs font-mono font-bold px-2 py-0.5 rounded-full"
                    style={{ backgroundColor: planColor(usage.plan) + '26', color: planColor(usage.plan) }}>
                    {usage.plan_label}
                  </span>
                  {isSuperAdmin && (
                    <span className="text-[10px] bg-[#ff2244]/15 text-[#ff2244] px-1.5 py-0.5 rounded-full">Superadmin — all limits bypassed</span>
                  )}
                </div>
                <div className="space-y-2">
                  {[
                    { label: 'Targets', current: usage.usage.targets, max: usage.limits.max_targets },
                    { label: 'Scans this month', current: usage.usage.scans_this_month, max: usage.limits.max_scans_per_month },
                  ].map(({ label, current, max }) => {
                    const unlimited = max === -1
                    const pct = unlimited ? (current > 0 ? 15 : 0) : Math.min((current / max) * 100, 100)
                    const color = unlimited ? '#00ff88' : pct >= 90 ? '#ff2244' : pct >= 70 ? '#ff8800' : '#00ff88'
                    return (
                      <div key={label} className="space-y-1">
                        <div className="flex justify-between text-xs">
                          <span className="text-gray-400">{label}</span>
                          <span className="font-mono text-gray-300">{current} / {unlimited ? '∞' : max}</span>
                        </div>
                        <div className="h-2 bg-[#0a0a0f] rounded-full overflow-hidden">
                          <div className="h-full rounded-full transition-all duration-500" style={{ width: `${unlimited ? 100 : pct}%`, backgroundColor: color, opacity: unlimited ? 0.3 : 1 }} />
                        </div>
                      </div>
                    )
                  })}
                </div>
                {/* Features */}
                {usage.features && (
                  <div>
                    <h4 className="text-xs font-semibold text-gray-500 mb-2">Features</h4>
                    <div className="grid grid-cols-2 gap-1.5">
                      {Object.entries(usage.features).map(([feat, enabled]) => (
                        <div key={feat} className="flex items-center gap-2 text-xs">
                          {enabled ? <CheckCircle className="w-3 h-3 text-[#00ff88]" /> : <XCircle className="w-3 h-3 text-gray-600" />}
                          <span className={enabled ? 'text-gray-300' : 'text-gray-600'}>{feat.replace(/_/g, ' ')}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
                {/* Plan cards */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3 pt-2">
                  {Object.entries(plans).map(([name, plan]) => {
                    const isCurrent = name === usage.plan
                    const color = planColor(name)
                    return (
                      <div key={name} className={`bg-[#0a0a0f] border rounded-xl p-4 ${isCurrent ? 'border-[' + color + ']/50' : 'border-[#1e1e2e]'}`}>
                        <div className="flex items-center justify-between mb-2">
                          <span className="text-sm font-bold" style={{ color }}>{plan.label}</span>
                          <span className="text-sm font-mono font-bold">{plan.price === 0 ? 'Free' : `€${plan.price}/mo`}</span>
                        </div>
                        <p className="text-[10px] text-gray-500 mb-2">{plan.description}</p>
                        <div className="text-[10px] text-gray-400 space-y-0.5 mb-3">
                          <div>{plan.max_targets === -1 ? '∞' : plan.max_targets} targets</div>
                          <div>{plan.max_scans_per_month === -1 ? '∞' : plan.max_scans_per_month} scans/mo</div>
                          <div>L{plan.allowed_layers.join('+L')}</div>
                        </div>
                        {isCurrent ? (
                          <span className="block text-center text-[10px] font-medium py-1.5 rounded-lg border border-[#1e1e2e] text-gray-500">Current</span>
                        ) : isSuperAdmin ? (
                          <button onClick={async () => {
                            if (!confirm(`Switch to ${name} plan?`)) return
                            setUpgrading(true)
                            try { await updateWorkspacePlan(activeWs.id, name); loadUsage(activeWs.id); loadWorkspaces() } catch (err) { alert(err.message) }
                            finally { setUpgrading(false) }
                          }} disabled={upgrading}
                            className="w-full text-center text-[10px] font-semibold py-1.5 rounded-lg transition-colors disabled:opacity-50"
                            style={{ backgroundColor: color + '26', color }}>
                            {upgrading ? '...' : (plans[usage.plan]?.price || 0) < plan.price ? 'Upgrade' : 'Switch'}
                          </button>
                        ) : (
                          <span className="block text-center text-[10px] text-gray-600 py-1.5">Contact admin</span>
                        )}
                      </div>
                    )
                  })}
                </div>
              </div>
            </div>
          )}

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
