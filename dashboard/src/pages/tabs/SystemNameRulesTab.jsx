import React, { useEffect, useState } from 'react'
import { getNameBlacklist, addNameBlacklist, removeNameBlacklist } from '../../lib/api'

export default function SystemNameRulesTab() {
  const [entries, setEntries] = useState([])
  const [loading, setLoading] = useState(true)
  const [newPattern, setNewPattern] = useState('')
  const [newType, setNewType] = useState('exact')
  const [newReason, setNewReason] = useState('')
  const [testName, setTestName] = useState('')
  const [testResult, setTestResult] = useState(null)

  useEffect(() => { loadEntries() }, [])

  async function loadEntries() {
    try {
      const data = await getNameBlacklist()
      setEntries(data.items || [])
    } catch {}
    finally { setLoading(false) }
  }

  async function handleAdd(e) {
    e.preventDefault()
    if (!newPattern.trim()) return
    try {
      await addNameBlacklist({ pattern: newPattern.trim(), type: newType, reason: newReason.trim() || null })
      setNewPattern('')
      setNewReason('')
      loadEntries()
    } catch (err) { alert(err.message) }
  }

  async function handleDelete(id) {
    try {
      await removeNameBlacklist(id)
      loadEntries()
    } catch (err) { alert(err.message) }
  }

  function handleTest(name) {
    setTestName(name)
    if (!name.trim() || name.trim().length < 3) {
      setTestResult({ blocked: true, reason: 'Too short (< 3 chars)' })
      return
    }
    const val = name.trim()
    const valLower = val.toLowerCase()
    for (const entry of entries) {
      const pattern = entry.pattern.toLowerCase()
      if (entry.type === 'exact' && valLower === pattern) {
        setTestResult({ blocked: true, reason: `Exact match: "${entry.pattern}" — ${entry.reason || ''}` })
        return
      }
      if (entry.type === 'contains' && valLower.includes(pattern)) {
        setTestResult({ blocked: true, reason: `Contains: "${entry.pattern}" — ${entry.reason || ''}` })
        return
      }
      if (entry.type === 'regex') {
        try {
          if (new RegExp(entry.pattern, 'i').test(val)) {
            setTestResult({ blocked: true, reason: `Regex: "${entry.pattern}" — ${entry.reason || ''}` })
            return
          }
        } catch {}
      }
    }
    setTestResult({ blocked: false })
  }

  if (loading) return <div className="text-gray-500 py-8 text-center">Loading name rules...</div>

  const typeColors = { exact: '#3388ff', contains: '#ffcc00', regex: '#ff8800' }

  return (
    <div className="space-y-4">
      <span className="text-xs text-gray-500 uppercase tracking-wider font-semibold">Name Blacklist Rules ({entries.length})</span>

      {/* Test input */}
      <div className="bg-[#12121a] border border-[#1e1e2e] rounded-xl p-4">
        <label className="text-xs text-gray-400 mb-2 block">Test a name against the blacklist</label>
        <div className="flex gap-3 items-center">
          <input type="text" value={testName} onChange={e => { handleTest(e.target.value) }}
            placeholder="Type a name to test..."
            className="flex-1 bg-[#0a0a0f] border border-[#1e1e2e] rounded-lg px-3 py-2 text-sm font-mono focus:outline-none focus:border-[#00ff88]/50" />
          {testResult && (
            <span className={`text-xs font-mono px-3 py-1.5 rounded-lg ${
              testResult.blocked ? 'bg-[#ff2244]/15 text-[#ff2244]' : 'bg-[#00ff88]/15 text-[#00ff88]'
            }`}>
              {testResult.blocked ? `BLOCKED — ${testResult.reason}` : 'OK — passes all rules'}
            </span>
          )}
        </div>
      </div>

      {/* Add form */}
      <form onSubmit={handleAdd} className="bg-[#12121a] border border-[#1e1e2e] rounded-xl p-4">
        <label className="text-xs text-gray-400 mb-2 block">Add new rule</label>
        <div className="flex gap-2 items-end">
          <div className="flex-1">
            <input type="text" value={newPattern} onChange={e => setNewPattern(e.target.value)} required placeholder="Pattern..."
              className="w-full bg-[#0a0a0f] border border-[#1e1e2e] rounded-lg px-3 py-2 text-sm font-mono focus:outline-none focus:border-[#00ff88]/50" />
          </div>
          <select value={newType} onChange={e => setNewType(e.target.value)}
            className="bg-[#0a0a0f] border border-[#1e1e2e] rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-[#00ff88]/50">
            <option value="exact">exact</option>
            <option value="contains">contains</option>
            <option value="regex">regex</option>
          </select>
          <div className="w-40">
            <input type="text" value={newReason} onChange={e => setNewReason(e.target.value)} placeholder="Reason..."
              className="w-full bg-[#0a0a0f] border border-[#1e1e2e] rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-[#00ff88]/50" />
          </div>
          <button type="submit" className="bg-[#00ff88] text-black font-semibold rounded-lg px-4 py-2 text-sm hover:bg-[#00ff88]/90">
            Add Rule
          </button>
        </div>
      </form>

      {/* Rules table */}
      <div className="bg-[#12121a] border border-[#1e1e2e] rounded-xl overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-xs text-gray-500 uppercase tracking-wider border-b border-[#1e1e2e]">
              <th className="text-left px-5 py-3">Pattern</th>
              <th className="text-left px-5 py-3">Type</th>
              <th className="text-left px-5 py-3">Reason</th>
              <th className="text-right px-5 py-3"></th>
            </tr>
          </thead>
          <tbody>
            {entries.map((e, i) => (
              <tr key={e.id} className={`border-t border-[#1e1e2e] ${i % 2 === 1 ? 'bg-white/[0.02]' : ''}`}>
                <td className="px-5 py-2 font-mono text-xs">{e.pattern}</td>
                <td className="px-5 py-2">
                  <span className="text-[10px] font-medium px-2 py-0.5 rounded"
                    style={{ backgroundColor: (typeColors[e.type] || '#666688') + '26', color: typeColors[e.type] || '#666688' }}>
                    {e.type}
                  </span>
                </td>
                <td className="px-5 py-2 text-xs text-gray-400">{e.reason || '-'}</td>
                <td className="px-5 py-2 text-right">
                  <button onClick={() => handleDelete(e.id)} className="text-xs text-gray-500 hover:text-[#ff2244]">Delete</button>
                </td>
              </tr>
            ))}
            {entries.length === 0 && (
              <tr><td colSpan={4} className="px-5 py-8 text-center text-gray-500">No rules defined</td></tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}
