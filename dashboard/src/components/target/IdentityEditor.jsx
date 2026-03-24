import { useState, useRef, useEffect } from 'react'
import { updateTargetIdentity } from '../../lib/api'

export default function IdentityEditor({ targetId, userFirstName, userLastName, autoResolvedName, displayName, onUpdate }) {
  const [editing, setEditing] = useState(false)
  const [firstName, setFirstName] = useState(userFirstName || '')
  const [lastName, setLastName] = useState(userLastName || '')
  const [saving, setSaving] = useState(false)
  const [saved, setSaved] = useState(false)
  const firstRef = useRef(null)

  const isOperatorSet = !!(userFirstName || userLastName)
  const currentName = displayName || autoResolvedName || ''

  // Auto-resolve placeholder: show what the system found
  const autoFirst = autoResolvedName ? autoResolvedName.split(' ').slice(0, -1).join(' ') || autoResolvedName : ''
  const autoLast = autoResolvedName ? autoResolvedName.split(' ').slice(-1)[0] || '' : ''

  useEffect(() => {
    if (editing && firstRef.current) firstRef.current.focus()
  }, [editing])

  // Sync props when parent updates
  useEffect(() => {
    setFirstName(userFirstName || '')
    setLastName(userLastName || '')
  }, [userFirstName, userLastName])

  const handleSave = async () => {
    setSaving(true)
    try {
      const f = firstName.trim() || null
      const l = lastName.trim() || null
      const res = await updateTargetIdentity(targetId, f, l)
      onUpdate?.(res)
      setEditing(false)
      setSaved(true)
      setTimeout(() => setSaved(false), 1500)
    } catch (e) {
      console.error('Failed to update identity:', e)
    } finally {
      setSaving(false)
    }
  }

  const handleClear = async () => {
    setSaving(true)
    try {
      const res = await updateTargetIdentity(targetId, null, null)
      setFirstName('')
      setLastName('')
      onUpdate?.(res)
      setEditing(false)
      setSaved(true)
      setTimeout(() => setSaved(false), 1500)
    } catch (e) {
      console.error('Failed to clear identity:', e)
    } finally {
      setSaving(false)
    }
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter') handleSave()
    if (e.key === 'Escape') { setEditing(false); setFirstName(userFirstName || ''); setLastName(userLastName || '') }
  }

  if (editing) {
    return (
      <div className="flex items-center gap-2 flex-wrap">
        <div className="flex items-center gap-1.5">
          <label className="text-[10px] text-gray-500 uppercase">First</label>
          <input
            ref={firstRef}
            value={firstName}
            onChange={(e) => setFirstName(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={autoFirst || 'First name'}
            maxLength={100}
            className="bg-[#0a0a0f] border border-[#2a2a3e] rounded px-2 py-1 text-sm font-mono text-gray-200 w-32 focus:border-[#3388ff] focus:outline-none placeholder-gray-600"
          />
        </div>
        <div className="flex items-center gap-1.5">
          <label className="text-[10px] text-gray-500 uppercase">Last</label>
          <input
            value={lastName}
            onChange={(e) => setLastName(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={autoLast || 'Last name'}
            maxLength={100}
            className="bg-[#0a0a0f] border border-[#2a2a3e] rounded px-2 py-1 text-sm font-mono text-gray-200 w-32 focus:border-[#3388ff] focus:outline-none placeholder-gray-600"
          />
        </div>
        <button onClick={handleSave} disabled={saving}
          className="px-2 py-1 text-[10px] font-mono rounded bg-[#00ff88]/15 text-[#00ff88] hover:bg-[#00ff88]/25 disabled:opacity-50 transition-colors">
          {saving ? '...' : 'Save'}
        </button>
        {isOperatorSet && (
          <button onClick={handleClear} disabled={saving}
            className="px-2 py-1 text-[10px] font-mono rounded bg-[#ff2244]/10 text-[#ff2244] hover:bg-[#ff2244]/20 disabled:opacity-50 transition-colors">
            Clear
          </button>
        )}
        <button onClick={() => { setEditing(false); setFirstName(userFirstName || ''); setLastName(userLastName || '') }}
          className="px-2 py-1 text-[10px] font-mono rounded bg-[#1e1e2e] text-gray-400 hover:bg-[#2a2a3e] transition-colors">
          Cancel
        </button>
      </div>
    )
  }

  return (
    <div className="flex items-center gap-2">
      {currentName ? (
        <>
          <h2 className="text-xl font-semibold">{currentName}</h2>
          <span title={isOperatorSet ? 'Operator-asserted name' : 'Auto-resolved name'}
            className="cursor-help text-sm">
            {isOperatorSet ? '\uD83D\uDC64' : '\uD83E\uDD16'}
          </span>
        </>
      ) : (
        <h2 className="text-xl text-gray-500 italic">Unknown identity</h2>
      )}
      <button onClick={() => setEditing(true)}
        className="text-gray-500 hover:text-[#3388ff] transition-colors text-sm" title="Edit identity">
        ✏️
      </button>
      {saved && <span className="text-[10px] text-[#00ff88] font-mono animate-pulse">Saved</span>}
    </div>
  )
}
