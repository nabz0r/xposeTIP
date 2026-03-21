import { useEffect, useState } from 'react'
import { Key, Cpu, SlidersHorizontal, User, Database, CheckCircle, XCircle, Loader2, Lock, Trash2, AlertTriangle, Plus } from 'lucide-react'
import { getModules, patchModule, getApiKeys, saveApiKey, validateApiKey, deleteApiKey, saveCustomKey, getDefaults, updateDefaults, getTargets, changePassword } from '../lib/api'
import { useAuth } from '../lib/auth'

const tabs = [
  { id: 'apikeys', label: 'API Keys', icon: Key },
  { id: 'modules', label: 'Scanner Modules', icon: Cpu },
  { id: 'defaults', label: 'Scan Defaults', icon: SlidersHorizontal },
  { id: 'profile', label: 'Profile & Security', icon: User },
  { id: 'data', label: 'Data Management', icon: Database },
]

const healthColors = { healthy: '#00ff88', unhealthy: '#ff2244', unknown: '#666688' }

export default function Settings() {
  const [activeTab, setActiveTab] = useState('apikeys')
  const { user } = useAuth()

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Settings</h1>

      {/* Tabs */}
      <div className="flex gap-1 border-b border-[#1e1e2e] overflow-x-auto">
        {tabs.map(tab => {
          const Icon = tab.icon
          return (
            <button key={tab.id} onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-2 px-4 py-2.5 text-sm whitespace-nowrap transition-colors ${
                activeTab === tab.id ? 'text-[#00ff88] border-b-2 border-[#00ff88]' : 'text-gray-400 hover:text-white'
              }`}>
              <Icon className="w-4 h-4" /> {tab.label}
            </button>
          )
        })}
      </div>

      {activeTab === 'apikeys' && <ApiKeysTab />}
      {activeTab === 'modules' && <ModulesTab />}
      {activeTab === 'defaults' && <DefaultsTab />}
      {activeTab === 'profile' && <ProfileTab user={user} />}
      {activeTab === 'data' && <DataTab />}
    </div>
  )
}

// ===================== API Keys Tab =====================
function ApiKeysTab() {
  const [keys, setKeys] = useState([])
  const [inputs, setInputs] = useState({})
  const [validating, setValidating] = useState({})
  const [saving, setSaving] = useState({})
  const [showCustom, setShowCustom] = useState(false)
  const [customName, setCustomName] = useState('')
  const [customValue, setCustomValue] = useState('')
  const [customDesc, setCustomDesc] = useState('')
  const [customSaving, setCustomSaving] = useState(false)

  useEffect(() => { loadKeys() }, [])

  async function loadKeys() {
    try {
      const data = await getApiKeys()
      setKeys(data)
    } catch {}
  }

  async function handleSave(keyName) {
    const value = inputs[keyName]
    if (!value) return
    setSaving(s => ({ ...s, [keyName]: true }))
    try {
      await saveApiKey(keyName, value)
      setInputs(i => ({ ...i, [keyName]: '' }))
      loadKeys()
    } catch (err) { alert(err.message) }
    finally { setSaving(s => ({ ...s, [keyName]: false })) }
  }

  async function handleValidate(keyName) {
    setValidating(v => ({ ...v, [keyName]: true }))
    try {
      const result = await validateApiKey(keyName)
      loadKeys()
      alert(result.message)
    } catch (err) { alert(err.message) }
    finally { setValidating(v => ({ ...v, [keyName]: false })) }
  }

  async function handleDelete(keyName) {
    if (!confirm(`Remove ${keyName}?`)) return
    try {
      await deleteApiKey(keyName)
      loadKeys()
    } catch (err) { alert(err.message) }
  }

  async function handleSaveCustom(e) {
    e.preventDefault()
    if (!customName || !customValue) return
    setCustomSaving(true)
    try {
      await saveCustomKey({ key_name: customName.toUpperCase().replace(/[^A-Z0-9_]/g, '_'), key_value: customValue, description: customDesc })
      setCustomName(''); setCustomValue(''); setCustomDesc('')
      setShowCustom(false)
      loadKeys()
    } catch (err) { alert(err.message) }
    finally { setCustomSaving(false) }
  }

  // Group keys: active scanners, future integrations, custom
  const activeKeys = keys.filter(k => !k.custom && k.has_module)
  const futureKeys = keys.filter(k => !k.custom && !k.has_module)
  const customKeys = keys.filter(k => k.custom)

  function KeyCard({ k }) {
    return (
      <div className="bg-[#12121a] border border-[#1e1e2e] rounded-xl p-5">
        <div className="flex items-center justify-between mb-3">
          <div>
            <div className="flex items-center gap-2 flex-wrap">
              <span className="text-sm font-semibold">{k.service_name || k.key_name}</span>
              {k.configured && k.valid === true && <CheckCircle className="w-4 h-4 text-[#00ff88]" />}
              {k.configured && k.valid === false && <XCircle className="w-4 h-4 text-[#ff2244]" />}
              {k.configured && k.valid == null && <span className="text-[10px] text-[#ffcc00]">Not validated</span>}
              {!k.configured && <span className="text-[10px] text-gray-500">Not configured</span>}
              {k.free === true && <span className="text-[10px] bg-[#00ff88]/15 text-[#00ff88] px-1.5 py-0.5 rounded-full">Free</span>}
              {k.free === false && <span className="text-[10px] bg-[#ff8800]/15 text-[#ff8800] px-1.5 py-0.5 rounded-full">Paid</span>}
            </div>
            <p className="text-xs text-gray-500 mt-0.5">{k.description}</p>
            <div className="flex items-center gap-3 mt-1">
              {k.module_id && (
                <span className="text-[10px] text-gray-600 inline-flex items-center gap-1">
                  <Cpu className="w-3 h-3" /> Powers: {k.module_id}
                </span>
              )}
              {!k.has_module && !k.custom && (
                <span className="text-[10px] text-gray-600">No module yet — coming soon</span>
              )}
              {k.url && (
                <a href={k.url} target="_blank" rel="noreferrer" className="text-[10px] text-[#3388ff] hover:underline">
                  Get key &rarr;
                </a>
              )}
            </div>
          </div>
          <div className="flex items-center gap-2 shrink-0">
            {k.source === 'env' && <span className="text-xs bg-[#3388ff]/15 text-[#3388ff] px-2 py-0.5 rounded">ENV</span>}
          </div>
        </div>

        <div className="flex gap-2">
          <input type="password" value={inputs[k.key_name] || ''}
            onChange={e => setInputs(i => ({ ...i, [k.key_name]: e.target.value }))}
            placeholder={k.masked || 'Enter API key...'}
            className="flex-1 bg-[#0a0a0f] border border-[#1e1e2e] rounded-lg px-3 py-2 text-sm font-mono focus:outline-none focus:border-[#00ff88]/50" />
          <button onClick={() => handleSave(k.key_name)} disabled={!inputs[k.key_name] || saving[k.key_name]}
            className="bg-[#00ff88] text-black font-semibold rounded-lg px-4 py-2 text-sm hover:bg-[#00ff88]/90 disabled:opacity-50">
            {saving[k.key_name] ? '...' : 'Save'}
          </button>
          {k.has_module && (
            <button onClick={() => handleValidate(k.key_name)} disabled={validating[k.key_name]}
              className="border border-[#1e1e2e] rounded-lg px-4 py-2 text-sm text-gray-300 hover:bg-white/5 disabled:opacity-50">
              {validating[k.key_name] ? <Loader2 className="w-4 h-4 animate-spin" /> : 'Validate'}
            </button>
          )}
          {k.configured && k.source !== 'env' && (
            <button onClick={() => handleDelete(k.key_name)} className="text-gray-500 hover:text-[#ff2244] px-2">
              <Trash2 className="w-4 h-4" />
            </button>
          )}
        </div>

        {k.last_validated && (
          <p className="text-[10px] text-gray-600 mt-2">Validated: {new Date(k.last_validated).toLocaleString()}</p>
        )}
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Active Scanner Keys */}
      <div>
        <h3 className="text-xs font-semibold uppercase tracking-wider text-gray-500 mb-3">
          Active Scanners ({activeKeys.filter(k => k.configured).length}/{activeKeys.length} configured)
        </h3>
        <div className="space-y-3">
          {activeKeys.map(k => <KeyCard key={k.key_name} k={k} />)}
        </div>
      </div>

      {/* Future Integration Keys */}
      {futureKeys.length > 0 && (
        <div>
          <h3 className="text-xs font-semibold uppercase tracking-wider text-gray-500 mb-3">
            Future Integrations — configure now, use when scanners ship
          </h3>
          <div className="space-y-3">
            {futureKeys.map(k => <KeyCard key={k.key_name} k={k} />)}
          </div>
        </div>
      )}

      {/* Custom Keys */}
      <div>
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-xs font-semibold uppercase tracking-wider text-gray-500">Custom API Keys</h3>
          <button onClick={() => setShowCustom(true)}
            className="flex items-center gap-1.5 text-xs text-[#00ff88] hover:underline">
            <Plus className="w-3 h-3" /> Add custom key
          </button>
        </div>
        <div className="space-y-3">
          {customKeys.map(k => <KeyCard key={k.key_name} k={k} />)}
          {customKeys.length === 0 && !showCustom && (
            <p className="text-xs text-gray-600">No custom keys. Add keys for community plugins or external services.</p>
          )}
        </div>
      </div>

      {/* Add Custom Key Modal */}
      {showCustom && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50" onClick={() => setShowCustom(false)}>
          <div className="bg-[#12121a] border border-[#1e1e2e] rounded-xl p-6 w-full max-w-md" onClick={e => e.stopPropagation()}>
            <h2 className="text-lg font-semibold mb-4">Add Custom API Key</h2>
            <form onSubmit={handleSaveCustom} className="space-y-4">
              <div>
                <label className="text-xs text-gray-400 mb-1 block">Key Name</label>
                <input type="text" value={customName} onChange={e => setCustomName(e.target.value)} required
                  placeholder="e.g. SHODAN_API_KEY"
                  className="w-full bg-[#0a0a0f] border border-[#1e1e2e] rounded-lg px-3 py-2 text-sm font-mono focus:outline-none focus:border-[#00ff88]/50 uppercase" />
              </div>
              <div>
                <label className="text-xs text-gray-400 mb-1 block">Description</label>
                <input type="text" value={customDesc} onChange={e => setCustomDesc(e.target.value)}
                  placeholder="What is this key used for?"
                  className="w-full bg-[#0a0a0f] border border-[#1e1e2e] rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-[#00ff88]/50" />
              </div>
              <div>
                <label className="text-xs text-gray-400 mb-1 block">API Key Value</label>
                <input type="password" value={customValue} onChange={e => setCustomValue(e.target.value)} required
                  placeholder="Enter API key..."
                  className="w-full bg-[#0a0a0f] border border-[#1e1e2e] rounded-lg px-3 py-2 text-sm font-mono focus:outline-none focus:border-[#00ff88]/50" />
              </div>
              <div className="flex gap-3 justify-end">
                <button type="button" onClick={() => setShowCustom(false)} className="px-4 py-2 text-sm text-gray-400 hover:text-white">Cancel</button>
                <button type="submit" disabled={customSaving || !customName || !customValue}
                  className="bg-[#00ff88] text-black font-semibold rounded-lg px-6 py-2 text-sm hover:bg-[#00ff88]/90 disabled:opacity-50">
                  {customSaving ? 'Saving...' : 'Save Key'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}

// ===================== Modules Tab =====================
function ModulesTab() {
  const [modules, setModules] = useState([])

  useEffect(() => {
    getModules().then(setModules).catch(() => {})
  }, [])

  async function toggleModule(id, forcedState) {
    const mod = modules.find(m => m.id === id)
    const newState = forcedState !== undefined ? forcedState : !mod.enabled
    try {
      const updated = await patchModule(id, { enabled: newState })
      setModules(prev => prev.map(m => m.id === id ? updated : m))
    } catch (err) { alert(err.message) }
  }

  const layers = [...new Set(modules.map(m => m.layer))].sort()

  return (
    <div className="space-y-4">
      {layers.map(layer => {
        const layerMods = modules.filter(m => m.layer === layer)
        const allEnabled = layerMods.filter(m => m.implemented).every(m => m.enabled)
        return (
          <div key={layer}>
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-xs font-semibold uppercase tracking-wider text-gray-500">Layer {layer}</h3>
              <button
                onClick={() => {
                  const newEnabled = !allEnabled
                  layerMods.filter(m => m.implemented).forEach(mod => toggleModule(mod.id, newEnabled))
                }}
                className="text-[10px] px-2 py-0.5 rounded border border-[#1e1e2e] text-gray-400 hover:text-[#00ff88] hover:border-[#00ff88]/30 transition-colors"
              >
                {allEnabled ? 'Disable All' : 'Enable All'}
              </button>
            </div>
            <div className="bg-[#12121a] border border-[#1e1e2e] rounded-xl overflow-hidden divide-y divide-[#1e1e2e]">
              {layerMods.map(mod => (
                <div key={mod.id} className={`flex items-center justify-between px-5 py-4 ${!mod.implemented ? 'opacity-50' : ''}`}>
                  <div className="flex items-center gap-4">
                    <div className="w-2 h-2 rounded-full" style={{ backgroundColor: healthColors[mod.health_status] || '#666688' }} />
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="text-sm font-medium">{mod.display_name}</span>
                        {!mod.implemented && <span className="text-[10px] bg-[#1e1e2e] text-gray-500 px-1.5 py-0.5 rounded">Coming soon</span>}
                        {mod.requires_auth && (
                          <span className="inline-flex items-center gap-1 text-[10px] px-1.5 py-0.5 rounded bg-[#ff8800]/10 text-[#ff8800]">
                            <Lock className="w-3 h-3" /> Requires API key
                          </span>
                        )}
                      </div>
                      <div className="text-xs text-gray-500 mt-0.5">{mod.description}</div>
                      <span className="text-[10px] px-1.5 py-0.5 rounded bg-white/5 text-gray-400">{mod.category}</span>
                    </div>
                  </div>
                  <button
                    onClick={() => toggleModule(mod.id, !mod.enabled)}
                    disabled={!mod.implemented}
                    className={`relative w-11 h-6 rounded-full transition-colors ${mod.enabled ? 'bg-[#00ff88]' : 'bg-[#1e1e2e]'} disabled:cursor-not-allowed`}>
                    <span className={`absolute top-0.5 left-0.5 w-5 h-5 rounded-full bg-white transition-transform ${mod.enabled ? 'translate-x-5' : ''}`} />
                  </button>
                </div>
              ))}
            </div>
          </div>
        )
      })}
    </div>
  )
}

// ===================== Scan Defaults Tab =====================
function DefaultsTab() {
  const [modules, setModules] = useState([])
  const [defaults, setDefaults] = useState({ default_modules: [], rate_limit: 1 })
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    Promise.all([getModules(), getDefaults()]).then(([mods, defs]) => {
      setModules(mods.filter(m => m.implemented))
      setDefaults(defs)
    }).catch(() => {})
  }, [])

  function toggleModule(id) {
    setDefaults(d => ({
      ...d,
      default_modules: d.default_modules.includes(id)
        ? d.default_modules.filter(m => m !== id)
        : [...d.default_modules, id],
    }))
  }

  async function handleSave() {
    setSaving(true)
    try {
      await updateDefaults(defaults)
      alert('Defaults saved')
    } catch (err) { alert(err.message) }
    finally { setSaving(false) }
  }

  return (
    <div className="space-y-5">
      <div className="bg-[#12121a] border border-[#1e1e2e] rounded-xl p-5">
        <h3 className="text-sm font-semibold mb-3">Default Modules for Quick Scan</h3>
        <p className="text-xs text-gray-500 mb-4">These modules are pre-selected when using Quick Scan on the Dashboard.</p>
        <div className="space-y-4">
          {[...new Set(modules.map(m => m.layer))].sort().map(layer => {
            const layerMods = modules.filter(m => m.layer === layer)
            const allSelected = layerMods.every(m => defaults.default_modules.includes(m.id))
            return (
              <div key={layer}>
                <div className="flex items-center justify-between mb-2">
                  <h3 className="text-xs font-semibold uppercase tracking-wider text-gray-500">Layer {layer}</h3>
                  <button
                    onClick={() => {
                      const layerIds = layerMods.map(m => m.id)
                      if (allSelected) {
                        setDefaults(d => ({ ...d, default_modules: d.default_modules.filter(id => !layerIds.includes(id)) }))
                      } else {
                        setDefaults(d => ({ ...d, default_modules: [...new Set([...d.default_modules, ...layerIds])] }))
                      }
                    }}
                    className="text-[10px] px-2 py-0.5 rounded border border-[#1e1e2e] text-gray-400 hover:text-[#00ff88] hover:border-[#00ff88]/30 transition-colors"
                  >
                    {allSelected ? 'Deselect All' : 'Select All'}
                  </button>
                </div>
                <div className="space-y-1.5">
                  {layerMods.map(mod => (
                    <label key={mod.id} className="flex items-center gap-3 px-3 py-2 rounded-lg hover:bg-white/5 cursor-pointer">
                      <input type="checkbox" checked={defaults.default_modules.includes(mod.id)}
                        onChange={() => toggleModule(mod.id)} className="accent-[#00ff88]" />
                      <span className="text-sm">{mod.display_name}</span>
                      <span className="text-[10px] text-gray-500 ml-auto">{mod.category}</span>
                    </label>
                  ))}
                </div>
              </div>
            )
          })}
        </div>
      </div>

      <div className="bg-[#12121a] border border-[#1e1e2e] rounded-xl p-5">
        <h3 className="text-sm font-semibold mb-3">Rate Limit</h3>
        <div className="flex items-center gap-4">
          <input type="range" min="0.5" max="5" step="0.5" value={defaults.rate_limit}
            onChange={e => setDefaults(d => ({ ...d, rate_limit: parseFloat(e.target.value) }))}
            className="flex-1 accent-[#00ff88]" />
          <span className="font-mono text-sm w-20 text-right">{defaults.rate_limit} req/s</span>
        </div>
      </div>

      <button onClick={handleSave} disabled={saving}
        className="bg-[#00ff88] text-black font-semibold rounded-lg px-6 py-2.5 text-sm hover:bg-[#00ff88]/90 disabled:opacity-50">
        {saving ? 'Saving...' : 'Save Defaults'}
      </button>
    </div>
  )
}

// ===================== Profile Tab =====================
function ProfileTab({ user }) {
  const [displayName, setDisplayName] = useState(user?.display_name || '')
  const [savingProfile, setSavingProfile] = useState(false)
  const [currentPw, setCurrentPw] = useState('')
  const [newPw, setNewPw] = useState('')
  const [confirmPw, setConfirmPw] = useState('')
  const [saving, setSaving] = useState(false)

  async function handleSaveProfile(e) {
    e.preventDefault()
    setSavingProfile(true)
    try {
      const { updateProfile } = await import('../lib/api')
      await updateProfile({ display_name: displayName })
      alert('Profile updated')
    } catch (err) { alert(err.message) }
    finally { setSavingProfile(false) }
  }

  async function handleChangePassword(e) {
    e.preventDefault()
    if (newPw !== confirmPw) { alert('Passwords do not match'); return }
    if (newPw.length < 8) { alert('Password must be at least 8 characters'); return }
    setSaving(true)
    try {
      await changePassword({ current_password: currentPw, new_password: newPw })
      setCurrentPw(''); setNewPw(''); setConfirmPw('')
      alert('Password changed successfully')
    } catch (err) { alert(err.message) }
    finally { setSaving(false) }
  }

  return (
    <div className="space-y-5">
      <div className="bg-[#12121a] border border-[#1e1e2e] rounded-xl p-5">
        <h3 className="text-sm font-semibold mb-4">Profile</h3>
        <form onSubmit={handleSaveProfile} className="space-y-3 max-w-sm">
          <div>
            <label className="text-xs text-gray-400 mb-1 block">Email</label>
            <input type="text" value={user?.email || ''} disabled
              className="w-full bg-[#0a0a0f] border border-[#1e1e2e] rounded-lg px-3 py-2 text-sm font-mono text-gray-500 cursor-not-allowed" />
          </div>
          <div>
            <label className="text-xs text-gray-400 mb-1 block">Display Name</label>
            <input type="text" value={displayName} onChange={e => setDisplayName(e.target.value)}
              placeholder="Your display name"
              className="w-full bg-[#0a0a0f] border border-[#1e1e2e] rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-[#00ff88]/50" />
          </div>
          <div className="flex justify-between items-center">
            <div className="text-xs text-gray-500">Role: <span className="text-[#00ff88]">{user?.workspaces?.[0]?.role || '-'}</span></div>
            <button type="submit" disabled={savingProfile}
              className="bg-[#00ff88] text-black font-semibold rounded-lg px-4 py-2 text-sm hover:bg-[#00ff88]/90 disabled:opacity-50">
              {savingProfile ? 'Saving...' : 'Save Profile'}
            </button>
          </div>
        </form>
      </div>

      <div className="bg-[#12121a] border border-[#1e1e2e] rounded-xl p-5">
        <h3 className="text-sm font-semibold mb-4">Change Password</h3>
        <form onSubmit={handleChangePassword} className="space-y-3 max-w-sm">
          <input type="password" value={currentPw} onChange={e => setCurrentPw(e.target.value)} placeholder="Current password" required
            className="w-full bg-[#0a0a0f] border border-[#1e1e2e] rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-[#00ff88]/50" />
          <input type="password" value={newPw} onChange={e => setNewPw(e.target.value)} placeholder="New password" required
            className="w-full bg-[#0a0a0f] border border-[#1e1e2e] rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-[#00ff88]/50" />
          <input type="password" value={confirmPw} onChange={e => setConfirmPw(e.target.value)} placeholder="Confirm new password" required
            className="w-full bg-[#0a0a0f] border border-[#1e1e2e] rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-[#00ff88]/50" />
          <button type="submit" disabled={saving}
            className="bg-[#00ff88] text-black font-semibold rounded-lg px-6 py-2 text-sm hover:bg-[#00ff88]/90 disabled:opacity-50">
            {saving ? 'Changing...' : 'Change Password'}
          </button>
        </form>
      </div>

      <div className="bg-[#12121a] border border-[#1e1e2e] rounded-xl p-5">
        <h3 className="text-sm font-semibold mb-2">Multi-factor Authentication</h3>
        <p className="text-xs text-gray-500">TOTP-based MFA coming soon.</p>
      </div>
    </div>
  )
}

// ===================== Data Management Tab =====================
function DataTab() {
  const [exporting, setExporting] = useState(false)
  const [deleteConfirm, setDeleteConfirm] = useState('')
  const [showDelete, setShowDelete] = useState(false)

  async function handleExport() {
    setExporting(true)
    try {
      const targets = await getTargets()
      const blob = new Blob([JSON.stringify(targets, null, 2)], { type: 'application/json' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `xpose-export-${new Date().toISOString().slice(0, 10)}.json`
      a.click()
      URL.revokeObjectURL(url)
    } catch (err) { alert(err.message) }
    finally { setExporting(false) }
  }

  return (
    <div className="space-y-5">
      <div className="bg-[#12121a] border border-[#1e1e2e] rounded-xl p-5">
        <h3 className="text-sm font-semibold mb-2">Export Data</h3>
        <p className="text-xs text-gray-500 mb-4">Download all your target data as JSON.</p>
        <button onClick={handleExport} disabled={exporting}
          className="border border-[#1e1e2e] rounded-lg px-4 py-2 text-sm text-gray-300 hover:bg-white/5 disabled:opacity-50">
          {exporting ? 'Exporting...' : 'Export All Data'}
        </button>
      </div>

      <div className="bg-[#12121a] border border-[#ff2244]/30 rounded-xl p-5">
        <div className="flex items-center gap-2 mb-2">
          <AlertTriangle className="w-4 h-4 text-[#ff2244]" />
          <h3 className="text-sm font-semibold text-[#ff2244]">Danger Zone</h3>
        </div>
        <p className="text-xs text-gray-500 mb-4">Permanently delete all data in this workspace. This action cannot be undone.</p>
        {!showDelete ? (
          <button onClick={() => setShowDelete(true)}
            className="border border-[#ff2244]/50 text-[#ff2244] rounded-lg px-4 py-2 text-sm hover:bg-[#ff2244]/10">
            Delete All My Data
          </button>
        ) : (
          <div className="space-y-3">
            <p className="text-xs text-gray-400">Type <span className="font-mono text-white">DELETE</span> to confirm:</p>
            <input type="text" value={deleteConfirm} onChange={e => setDeleteConfirm(e.target.value)}
              className="w-64 bg-[#0a0a0f] border border-[#ff2244]/30 rounded-lg px-3 py-2 text-sm font-mono focus:outline-none focus:border-[#ff2244]/50" />
            <div className="flex gap-2">
              <button disabled={deleteConfirm !== 'DELETE'}
                className="bg-[#ff2244] text-white font-semibold rounded-lg px-4 py-2 text-sm disabled:opacity-30">
                Permanently Delete
              </button>
              <button onClick={() => { setShowDelete(false); setDeleteConfirm('') }}
                className="text-sm text-gray-400 hover:text-white px-4 py-2">Cancel</button>
            </div>
          </div>
        )}
      </div>

      <div className="bg-[#12121a] border border-[#1e1e2e] rounded-xl p-5">
        <h3 className="text-sm font-semibold mb-2">Privacy</h3>
        <p className="text-xs text-gray-500">Your data is stored encrypted and never shared with third parties. All scans are performed on-premises within your infrastructure.</p>
      </div>
    </div>
  )
}
