import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Plus, Trash2, Search, Eye, Upload, Play } from 'lucide-react'
import { getTargets, createTarget, deleteTarget, bulkImportTargets, createScan } from '../lib/api'
import TargetQuickView from '../components/TargetQuickView'
import GenerativeAvatar from '../components/GenerativeAvatar'
import useSSE from '../hooks/useSSE'

const FLAG = (code) => {
  if (!code) return ''
  return String.fromCodePoint(...[...code.toUpperCase()].map(c => 0x1F1E6 + c.charCodeAt(0) - 65))
}

const scoreColor = (score) => {
  if (score == null) return '#666688'
  if (score >= 80) return '#ff2244'
  if (score >= 60) return '#ff8800'
  if (score >= 40) return '#ffcc00'
  if (score >= 20) return '#3388ff'
  return '#00ff88'
}

const fallbackSeed = (email) => {
  let hash = 0
  for (let i = 0; i < (email || '').length; i++) {
    hash = ((hash << 5) - hash) + email.charCodeAt(i)
    hash |= 0
  }
  return { email_hash: Math.abs(hash) }
}

const threatColor = (score) => {
  if (score == null) return '#666688'
  if (score >= 60) return '#ff2244'
  if (score >= 40) return '#ff8800'
  if (score >= 20) return '#ffcc00'
  return '#00ff88'
}

function MiniBar({ value, max = 100, color }) {
  const pct = Math.min(100, Math.max(0, (value / max) * 100))
  return (
    <div className="h-1.5 w-16 bg-[#0a0a0f] rounded-full overflow-hidden mt-0.5">
      <div className="h-full rounded-full transition-all duration-500" style={{ width: `${pct}%`, backgroundColor: color }} />
    </div>
  )
}

function formatTimestamp(iso) {
  if (!iso) return 'Never'
  const d = new Date(iso)
  const dd = String(d.getDate()).padStart(2, '0')
  const mm = String(d.getMonth() + 1).padStart(2, '0')
  const hh = String(d.getHours()).padStart(2, '0')
  const min = String(d.getMinutes()).padStart(2, '0')
  const ss = String(d.getSeconds()).padStart(2, '0')
  return `${dd}/${mm} ${hh}:${min}:${ss}`
}

export default function Targets() {
  const [targets, setTargets] = useState([])
  const [total, setTotal] = useState(0)
  const [search, setSearch] = useState('')
  const [showAdd, setShowAdd] = useState(false)
  const [showBulk, setShowBulk] = useState(false)
  const [newEmail, setNewEmail] = useState('')
  const [newCountry, setNewCountry] = useState('')
  const [bulkText, setBulkText] = useState('')
  const [bulkCountry, setBulkCountry] = useState('')
  const [bulkResult, setBulkResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [quickViewId, setQuickViewId] = useState(null)
  const [scanningIds, setScanningIds] = useState(new Set())
  const navigate = useNavigate()

  useEffect(() => {
    loadTargets()
  }, [search])
  useSSE({ 'scan.completed': () => loadTargets(), 'scan.started': () => loadTargets(), 'target.updated': () => loadTargets() })

  async function loadTargets() {
    try {
      const searchParam = search ? `search=${encodeURIComponent(search)}&` : ''
      const data = await getTargets(`${searchParam}per_page=100`)
      setTargets(data.items || [])
      setTotal(data.total || 0)
    } catch {}
  }

  async function handleAdd(e) {
    e.preventDefault()
    setLoading(true)
    try {
      await createTarget({ email: newEmail, country_code: newCountry || null })
      setShowAdd(false)
      setNewEmail('')
      setNewCountry('')
      loadTargets()
    } catch (err) {
      alert(err.message)
    } finally {
      setLoading(false)
    }
  }

  async function handleBulkImport(e) {
    e.preventDefault()
    setLoading(true)
    setBulkResult(null)
    try {
      const emails = bulkText
        .split(/[\n,;]+/)
        .map(e => e.trim().toLowerCase())
        .filter(e => e && e.includes('@'))
      if (emails.length === 0) { alert('No valid emails found'); return }
      const result = await bulkImportTargets({ emails, country_code: bulkCountry || null })
      setBulkResult(result)
      loadTargets()
    } catch (err) {
      alert(err.message)
    } finally {
      setLoading(false)
    }
  }

  async function handleDelete(e, id) {
    e.stopPropagation()
    if (!confirm('Delete this target and all associated data?')) return
    try {
      await deleteTarget(id)
      loadTargets()
    } catch (err) {
      alert(err.message)
    }
  }

  async function handleQuickScan(e, targetId) {
    e.stopPropagation()
    setScanningIds(prev => new Set([...prev, targetId]))
    try {
      await createScan({ target_id: targetId })
      loadTargets()
    } catch (err) {
      alert(err.message)
    } finally {
      setScanningIds(prev => {
        const next = new Set(prev)
        next.delete(targetId)
        return next
      })
    }
  }

  return (
    <div className="space-y-4 pb-8">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Targets <span className="text-sm text-gray-500 font-normal ml-2">{total}</span></h1>
        <div className="flex gap-2">
          <button onClick={() => setShowBulk(true)} className="flex items-center gap-2 bg-[#12121a] border border-[#1e1e2e] text-gray-300 font-medium rounded-lg px-4 py-2 text-sm hover:border-[#00ff88]/50">
            <Upload className="w-4 h-4" /> Bulk Import
          </button>
          <button onClick={() => setShowAdd(true)} className="flex items-center gap-2 bg-[#00ff88] text-black font-semibold rounded-lg px-4 py-2 text-sm hover:bg-[#00ff88]/90">
            <Plus className="w-4 h-4" /> Add Target
          </button>
        </div>
      </div>

      {/* Search */}
      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
        <input
          type="text"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search by email..."
          className="w-full bg-[#12121a] border border-[#1e1e2e] rounded-lg pl-10 pr-3 py-2.5 text-sm font-mono focus:outline-none focus:border-[#00ff88]/50"
        />
      </div>

      {/* Table */}
      <div className="bg-[#12121a] border border-[#1e1e2e] rounded-xl overflow-x-hidden overflow-y-auto max-h-[calc(100vh-240px)]">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-xs text-gray-500 uppercase tracking-wider border-b border-[#1e1e2e]">
              <th className="text-left px-5 py-3">Target</th>
              <th className="text-left px-3 py-3">Country</th>
              <th className="text-left px-3 py-3">Exposure</th>
              <th className="text-left px-3 py-3">Threat</th>
              <th className="text-left px-3 py-3">Last Scan</th>
              <th className="text-left px-3 py-3"></th>
            </tr>
          </thead>
          <tbody>
            {targets.map((t, i) => {
              const name = t.primary_name || t.display_name || ''
              const isScanning = t.status === 'scanning' || scanningIds.has(t.id)
              return (
                <tr
                  key={t.id}
                  onClick={() => navigate(`/targets/${t.id}`)}
                  className={`border-t border-[#1e1e2e] cursor-pointer hover:bg-white/[0.03] ${i % 2 === 1 ? 'bg-white/[0.02]' : ''}`}
                >
                  <td className="px-5 py-3">
                    <div className="flex items-center gap-3">
                      {t.avatar_url ? (
                        <img src={t.avatar_url} alt="" className="w-8 h-8 rounded-full border border-[#1e1e2e] shrink-0" />
                      ) : (
                        <GenerativeAvatar seed={t.fingerprint_avatar_seed || fallbackSeed(t.email)} size={36} score={t.exposure_score || 0} className="shrink-0" />
                      )}
                      <div className="min-w-0">
                        {name && <div className="text-sm font-medium truncate">{name}</div>}
                        <div className="text-xs font-mono text-gray-400 truncate">{t.email}</div>
                      </div>
                    </div>
                  </td>
                  <td className="px-3 py-3 text-xs">
                    {t.country_code ? `${FLAG(t.country_code)} ${t.country_code}` : <span className="text-gray-600">-</span>}
                  </td>
                  <td className="px-3 py-3">
                    {t.exposure_score != null ? (
                      <div>
                        <span className="font-mono font-bold text-sm" style={{ color: scoreColor(t.exposure_score) }}>
                          {t.exposure_score}
                        </span>
                        <MiniBar value={t.exposure_score} color={scoreColor(t.exposure_score)} />
                      </div>
                    ) : <span className="text-gray-600">-</span>}
                  </td>
                  <td className="px-3 py-3">
                    {t.threat_score != null ? (
                      <div>
                        <span className="font-mono font-bold text-sm" style={{ color: threatColor(t.threat_score) }}>
                          {t.threat_score}
                        </span>
                        <MiniBar value={t.threat_score} color={threatColor(t.threat_score)} />
                      </div>
                    ) : <span className="text-gray-600">-</span>}
                  </td>
                  <td className="px-3 py-3 text-xs font-mono text-gray-400">
                    {formatTimestamp(t.last_scanned)}
                  </td>
                  <td className="px-3 py-3">
                    <div className="flex items-center gap-1.5">
                      {!isScanning ? (
                        <button
                          onClick={(e) => handleQuickScan(e, t.id)}
                          className="text-[10px] px-2 py-1 rounded bg-[#00ff88]/10 text-[#00ff88] hover:bg-[#00ff88]/20 transition-colors"
                          title="Quick scan with default modules"
                        >
                          <Play className="w-3 h-3 inline mr-0.5" />Scan
                        </button>
                      ) : (
                        <span className="text-[10px] px-2 py-1 rounded bg-[#ffcc00]/10 text-[#ffcc00] animate-pulse">
                          Scanning...
                        </span>
                      )}
                      <button onClick={(e) => { e.stopPropagation(); setQuickViewId(t.id) }} className="text-gray-500 hover:text-[#00ff88] p-1" title="Quick view">
                        <Eye className="w-3.5 h-3.5" />
                      </button>
                      <button onClick={(e) => handleDelete(e, t.id)} className="text-gray-500 hover:text-[#ff2244] p-1" title="Delete">
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  </td>
                </tr>
              )
            })}
            {targets.length === 0 && (
              <tr><td colSpan={6} className="px-5 py-8 text-center text-gray-500">No targets found</td></tr>
            )}
          </tbody>
        </table>
      </div>

      {/* Quick View */}
      {quickViewId && <TargetQuickView targetId={quickViewId} onClose={() => setQuickViewId(null)} />}

      {/* Bulk Import Modal */}
      {showBulk && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50" onClick={() => { setShowBulk(false); setBulkResult(null) }}>
          <div className="bg-[#12121a] border border-[#1e1e2e] rounded-xl p-6 w-full max-w-lg" onClick={e => e.stopPropagation()}>
            <h2 className="text-lg font-semibold mb-4">Bulk Import Targets</h2>
            <form onSubmit={handleBulkImport} className="space-y-4">
              <div>
                <label className="text-xs text-gray-400 mb-1 block">Emails (one per line, or comma/semicolon separated)</label>
                <textarea value={bulkText} onChange={e => setBulkText(e.target.value)} rows={8} placeholder={"user1@example.com\nuser2@example.com\nuser3@example.com"}
                  className="w-full bg-[#0a0a0f] border border-[#1e1e2e] rounded-lg px-3 py-2 text-sm font-mono focus:outline-none focus:border-[#00ff88]/50 resize-none" />
              </div>
              <div>
                <label className="text-xs text-gray-400 mb-1 block">Country Code (optional, applies to all)</label>
                <input type="text" value={bulkCountry} onChange={e => setBulkCountry(e.target.value)} maxLength={2} placeholder="US"
                  className="w-full bg-[#0a0a0f] border border-[#1e1e2e] rounded-lg px-3 py-2 text-sm font-mono focus:outline-none focus:border-[#00ff88]/50 uppercase" />
              </div>
              {bulkResult && (
                <div className="bg-[#0a0a0f] border border-[#1e1e2e] rounded-lg p-3 text-sm">
                  <p className="text-[#00ff88]">{bulkResult.created} targets created</p>
                  {bulkResult.skipped > 0 && <p className="text-[#ffcc00]">{bulkResult.skipped} duplicates skipped</p>}
                </div>
              )}
              <div className="flex gap-3 justify-end">
                <button type="button" onClick={() => { setShowBulk(false); setBulkResult(null) }} className="px-4 py-2 text-sm text-gray-400 hover:text-white">Cancel</button>
                <button type="submit" disabled={loading} className="bg-[#00ff88] text-black font-semibold rounded-lg px-6 py-2 text-sm hover:bg-[#00ff88]/90 disabled:opacity-50">
                  {loading ? 'Importing...' : 'Import'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Add Target Modal */}
      {showAdd && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50" onClick={() => setShowAdd(false)}>
          <div className="bg-[#12121a] border border-[#1e1e2e] rounded-xl p-6 w-full max-w-md" onClick={e => e.stopPropagation()}>
            <h2 className="text-lg font-semibold mb-4">Add Target</h2>
            <form onSubmit={handleAdd} className="space-y-4">
              <div>
                <label className="text-xs text-gray-400 mb-1 block">Email</label>
                <input type="email" value={newEmail} onChange={e => setNewEmail(e.target.value)} required
                  className="w-full bg-[#0a0a0f] border border-[#1e1e2e] rounded-lg px-3 py-2 text-sm font-mono focus:outline-none focus:border-[#00ff88]/50" />
              </div>
              <div>
                <label className="text-xs text-gray-400 mb-1 block">Country Code (optional)</label>
                <input type="text" value={newCountry} onChange={e => setNewCountry(e.target.value)} maxLength={2} placeholder="US"
                  className="w-full bg-[#0a0a0f] border border-[#1e1e2e] rounded-lg px-3 py-2 text-sm font-mono focus:outline-none focus:border-[#00ff88]/50 uppercase" />
              </div>
              <div className="flex gap-3 justify-end">
                <button type="button" onClick={() => setShowAdd(false)} className="px-4 py-2 text-sm text-gray-400 hover:text-white">Cancel</button>
                <button type="submit" disabled={loading} className="bg-[#00ff88] text-black font-semibold rounded-lg px-6 py-2 text-sm hover:bg-[#00ff88]/90 disabled:opacity-50">
                  {loading ? 'Adding...' : 'Add'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
