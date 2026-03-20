import { useEffect, useState } from 'react'
import { getModules, patchModule } from '../lib/api'
import { useAuth } from '../lib/auth'

const healthColors = { healthy: '#00ff88', unhealthy: '#ff2244', unknown: '#666688' }

export default function Settings() {
  const [modules, setModules] = useState([])
  const { user } = useAuth()

  useEffect(() => {
    getModules().then(setModules).catch(() => {})
  }, [])

  async function toggleModule(id, enabled) {
    try {
      const updated = await patchModule(id, { enabled })
      setModules(modules.map(m => m.id === id ? updated : m))
    } catch (err) {
      alert(err.message)
    }
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Settings</h1>

      {/* Modules */}
      <div className="bg-[#12121a] border border-[#1e1e2e] rounded-xl overflow-hidden">
        <div className="px-5 py-4 border-b border-[#1e1e2e]">
          <h2 className="text-sm font-semibold">Scanner Modules</h2>
        </div>
        <div className="divide-y divide-[#1e1e2e]">
          {modules.map(mod => (
            <div key={mod.id} className="flex items-center justify-between px-5 py-4">
              <div className="flex items-center gap-4">
                <div className="w-2 h-2 rounded-full" style={{ backgroundColor: healthColors[mod.health_status] || '#666688' }} />
                <div>
                  <div className="text-sm font-medium">{mod.display_name}</div>
                  <div className="text-xs text-gray-500">{mod.description}</div>
                  <div className="flex items-center gap-2 mt-1">
                    <span className="text-xs px-1.5 py-0.5 rounded bg-white/5 text-gray-400">Layer {mod.layer}</span>
                    <span className="text-xs px-1.5 py-0.5 rounded bg-white/5 text-gray-400">{mod.category}</span>
                    {mod.requires_auth && <span className="text-xs px-1.5 py-0.5 rounded bg-[#ff8800]/10 text-[#ff8800]">Auth required</span>}
                  </div>
                </div>
              </div>
              <button
                onClick={() => toggleModule(mod.id, !mod.enabled)}
                className={`relative w-11 h-6 rounded-full transition-colors ${mod.enabled ? 'bg-[#00ff88]' : 'bg-[#1e1e2e]'}`}
              >
                <span className={`absolute top-0.5 left-0.5 w-5 h-5 rounded-full bg-white transition-transform ${mod.enabled ? 'translate-x-5' : ''}`} />
              </button>
            </div>
          ))}
        </div>
      </div>

      {/* Profile */}
      <div className="bg-[#12121a] border border-[#1e1e2e] rounded-xl p-5">
        <h2 className="text-sm font-semibold mb-4">Profile</h2>
        <div className="space-y-3 text-sm">
          <div className="flex justify-between">
            <span className="text-gray-400">Email</span>
            <span className="font-mono">{user?.email || '-'}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-400">Display Name</span>
            <span>{user?.display_name || '-'}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-400">Role</span>
            <span className="text-[#00ff88]">{user?.workspaces?.[0]?.role || '-'}</span>
          </div>
        </div>
      </div>
    </div>
  )
}
