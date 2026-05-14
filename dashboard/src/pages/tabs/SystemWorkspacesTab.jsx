import React, { useEffect, useState } from 'react'
import { adminListWorkspaces, updateWorkspacePlan } from '../../lib/api'
import { planColors } from '../../lib/planColors'

export default function SystemWorkspacesTab() {
  const [workspaces, setWorkspaces] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => { loadWorkspaces() }, [])

  async function loadWorkspaces() {
    try {
      const data = await adminListWorkspaces()
      setWorkspaces(data.items || [])
    } catch {}
    finally { setLoading(false) }
  }

  async function handlePlanChange(wsId, newPlan) {
    try {
      await updateWorkspacePlan(wsId, newPlan)
      loadWorkspaces()
    } catch (err) { alert(err.message) }
  }

  if (loading) return <div className="text-gray-500 py-8 text-center">Loading workspaces...</div>

  return (
    <div className="space-y-4">
      <span className="text-xs text-gray-500 uppercase tracking-wider font-semibold">All Workspaces ({workspaces.length})</span>

      <div className="bg-[#12121a] border border-[#1e1e2e] rounded-xl overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-xs text-gray-500 uppercase tracking-wider border-b border-[#1e1e2e]">
              <th className="text-left px-5 py-3">Name</th>
              <th className="text-left px-5 py-3">Plan</th>
              <th className="text-right px-5 py-3">Members</th>
              <th className="text-right px-5 py-3">Targets</th>
              <th className="text-right px-5 py-3">Scans</th>
              <th className="text-left px-5 py-3">Created</th>
            </tr>
          </thead>
          <tbody>
            {workspaces.map((ws, i) => (
              <tr key={ws.id} className={`border-t border-[#1e1e2e] ${i % 2 === 1 ? 'bg-white/[0.02]' : ''}`}>
                <td className="px-5 py-3">
                  <div className="font-medium">{ws.name}</div>
                  <div className="text-[10px] text-gray-600 font-mono">{ws.slug}</div>
                </td>
                <td className="px-5 py-3">
                  <select value={ws.plan} onChange={e => handlePlanChange(ws.id, e.target.value)}
                    className="bg-[#0a0a0f] border border-[#1e1e2e] rounded px-2 py-1 text-xs focus:outline-none focus:border-[#00ff88]/50"
                    style={{ color: planColors[ws.plan] || '#666688' }}>
                    <option value="free">free</option>
                    <option value="starter">starter</option>
                    <option value="team">team</option>
                    <option value="enterprise">enterprise</option>
                  </select>
                </td>
                <td className="px-5 py-3 text-right font-mono">{ws.member_count}</td>
                <td className="px-5 py-3 text-right font-mono">{ws.target_count}</td>
                <td className="px-5 py-3 text-right font-mono">{ws.scan_count}</td>
                <td className="px-5 py-3 text-xs text-gray-500">
                  {ws.created_at ? new Date(ws.created_at).toLocaleDateString() : '-'}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
