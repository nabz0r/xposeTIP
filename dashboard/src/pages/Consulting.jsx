import { useEffect, useMemo, useState } from 'react'
import { Briefcase, Download, Trash2, AlertCircle, Loader2 } from 'lucide-react'
import {
  createConsultingCase,
  deleteConsultingCase,
  downloadConsultingCase,
  getTargets,
  listConsultingCases,
} from '../lib/api'

const TIERS = [
  {
    key: 'quick',
    label: 'Quick Profile',
    price: '€2 500',
    range: '1 identifier',
    sla: '24–48h',
    min: 1,
    max: 1,
  },
  {
    key: 'assessment',
    label: 'Identity Assessment',
    price: '€6 500',
    range: '2–3 identifiers',
    sla: '48–72h',
    min: 2,
    max: 3,
  },
  {
    key: 'deep',
    label: 'Deep Investigation',
    price: '€15 000',
    range: '5–10 identifiers',
    sla: '5–10 days',
    min: 5,
    max: 10,
  },
]

function defaultDeadline() {
  const d = new Date()
  d.setDate(d.getDate() + 7)
  return d.toISOString().slice(0, 10)
}

function formatTimestamp(iso) {
  if (!iso) return '—'
  try {
    return new Date(iso).toLocaleString()
  } catch {
    return iso
  }
}

export default function Consulting() {
  const [targets, setTargets] = useState([])
  const [cases, setCases] = useState([])
  const [loadingTargets, setLoadingTargets] = useState(true)
  const [loadingCases, setLoadingCases] = useState(true)
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [confirmDelete, setConfirmDelete] = useState(null)

  const [tier, setTier] = useState('quick')
  const [clientName, setClientName] = useState('')
  const [scope, setScope] = useState('')
  const [deadline, setDeadline] = useState(defaultDeadline())
  const [pickedIds, setPickedIds] = useState([])
  const [primaryId, setPrimaryId] = useState('')

  const tierMeta = TIERS.find(t => t.key === tier) || TIERS[0]

  async function refreshCases() {
    setLoadingCases(true)
    try {
      const data = await listConsultingCases()
      setCases(Array.isArray(data) ? data : [])
    } catch (err) {
      setError(err.message || 'Failed to load cases')
    } finally {
      setLoadingCases(false)
    }
  }

  async function refreshTargets() {
    setLoadingTargets(true)
    try {
      const data = await getTargets('per_page=500')
      const items = Array.isArray(data) ? data : (data?.items || [])
      setTargets(items)
    } catch (err) {
      setError(err.message || 'Failed to load targets')
    } finally {
      setLoadingTargets(false)
    }
  }

  useEffect(() => {
    refreshTargets()
    refreshCases()
  }, [])

  useEffect(() => {
    setPickedIds(prev => prev.slice(0, tierMeta.max))
  }, [tier])

  useEffect(() => {
    if (pickedIds.length === 0) {
      setPrimaryId('')
    } else if (!pickedIds.includes(primaryId)) {
      setPrimaryId(pickedIds[0])
    }
  }, [pickedIds])

  const scannedTargets = useMemo(
    () => targets.filter(t => t.profile_data || t.last_scanned),
    [targets],
  )

  function togglePick(id) {
    setPickedIds(prev => {
      if (prev.includes(id)) return prev.filter(x => x !== id)
      if (prev.length >= tierMeta.max) return prev
      return [...prev, id]
    })
  }

  const countOk = pickedIds.length >= tierMeta.min && pickedIds.length <= tierMeta.max
  const formOk = countOk && clientName.trim() && scope.trim() && deadline && primaryId

  async function handleSubmit(e) {
    e?.preventDefault?.()
    setError('')
    if (!formOk) {
      setError('Fill all required fields and pick the correct number of identifiers.')
      return
    }
    setSubmitting(true)
    try {
      const resp = await createConsultingCase({
        tier,
        client_name: clientName.trim(),
        scope: scope.trim(),
        deadline,
        target_ids: pickedIds,
        primary_target_id: primaryId,
      })
      if (resp?.report_id) {
        try {
          await downloadConsultingCase(resp.report_id)
        } catch (err) {
          console.warn('Download after create failed', err)
        }
      }
      setClientName('')
      setScope('')
      setDeadline(defaultDeadline())
      setPickedIds([])
      setPrimaryId('')
      await refreshCases()
    } catch (err) {
      setError(err.message || 'Failed to create case')
    } finally {
      setSubmitting(false)
    }
  }

  async function handleDelete(id) {
    try {
      await deleteConsultingCase(id)
      setConfirmDelete(null)
      await refreshCases()
    } catch (err) {
      setError(err.message || 'Failed to delete case')
    }
  }

  return (
    <div className="max-w-6xl space-y-6">
      <header className="flex items-center gap-3">
        <Briefcase className="w-6 h-6 text-[#3388ff]" />
        <div>
          <h1 className="text-2xl font-bold text-white">Consulting</h1>
          <p className="text-sm text-gray-500">
            Generate Markdown drafts of Play-1 consulting tiers from scanned targets.
          </p>
        </div>
      </header>

      {error && (
        <div className="flex items-start gap-2 p-3 rounded-lg border border-[#ff2244]/30 bg-[#ff2244]/10 text-[#ff2244] text-sm">
          <AlertCircle className="w-4 h-4 mt-0.5 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* New case form */}
      <section className="bg-[#12121a] border border-[#1e1e2e] rounded-xl p-5 space-y-5">
        <h2 className="text-sm font-semibold text-gray-300 uppercase tracking-wide">New case</h2>

        {/* Tier selector */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          {TIERS.map(t => (
            <button
              key={t.key}
              type="button"
              onClick={() => setTier(t.key)}
              className={`text-left p-4 rounded-lg border transition-colors ${
                tier === t.key
                  ? 'border-[#3388ff] bg-[#3388ff]/10'
                  : 'border-[#1e1e2e] bg-[#0a0a0f] hover:border-[#3388ff]/50'
              }`}
            >
              <div className="flex items-center justify-between">
                <span className="font-semibold text-white">{t.label}</span>
                <span className="text-xs font-mono text-[#3388ff]">{t.price}</span>
              </div>
              <div className="text-xs text-gray-500 mt-1">{t.range} · {t.sla}</div>
            </button>
          ))}
        </div>

        {/* Meta fields */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="block text-xs uppercase text-gray-500 mb-1">Client name *</label>
            <input
              type="text"
              value={clientName}
              onChange={e => setClientName(e.target.value)}
              className="w-full px-3 py-2 rounded-lg bg-[#0a0a0f] border border-[#1e1e2e] text-sm text-white focus:border-[#3388ff] outline-none"
              placeholder="Acme DD"
              required
            />
          </div>
          <div>
            <label className="block text-xs uppercase text-gray-500 mb-1">Deadline *</label>
            <input
              type="date"
              value={deadline}
              onChange={e => setDeadline(e.target.value)}
              className="w-full px-3 py-2 rounded-lg bg-[#0a0a0f] border border-[#1e1e2e] text-sm text-white focus:border-[#3388ff] outline-none"
              required
            />
          </div>
          <div>
            <label className="block text-xs uppercase text-gray-500 mb-1">Primary target *</label>
            <select
              value={primaryId}
              onChange={e => setPrimaryId(e.target.value)}
              disabled={pickedIds.length === 0}
              className="w-full px-3 py-2 rounded-lg bg-[#0a0a0f] border border-[#1e1e2e] text-sm text-white focus:border-[#3388ff] outline-none disabled:opacity-50"
            >
              {pickedIds.length === 0 && <option value="">— pick a target first —</option>}
              {pickedIds.map(id => {
                const t = targets.find(x => x.id === id)
                return <option key={id} value={id}>{t?.email || id}</option>
              })}
            </select>
          </div>
        </div>

        <div>
          <label className="block text-xs uppercase text-gray-500 mb-1">Scope *</label>
          <textarea
            value={scope}
            onChange={e => setScope(e.target.value)}
            rows={2}
            className="w-full px-3 py-2 rounded-lg bg-[#0a0a0f] border border-[#1e1e2e] text-sm text-white focus:border-[#3388ff] outline-none"
            placeholder="Pre-acquisition diligence on subject X"
            required
          />
        </div>

        {/* Target picker */}
        <div>
          <div className="flex items-center justify-between mb-2">
            <label className="text-xs uppercase text-gray-500">
              Identifiers
              <span className={`ml-2 font-mono ${countOk ? 'text-[#00ff88]' : 'text-[#ff2244]'}`}>
                {pickedIds.length}/{tierMeta.max}
              </span>
              <span className="ml-2 text-gray-600">({tierMeta.min}–{tierMeta.max} required)</span>
            </label>
            <span className="text-xs text-gray-500">
              {loadingTargets ? 'loading…' : `${scannedTargets.length}/${targets.length} scanned`}
            </span>
          </div>
          <div className={`border rounded-lg max-h-72 overflow-y-auto ${
            countOk ? 'border-[#00ff88]/40' : 'border-[#1e1e2e]'
          }`}>
            {targets.length === 0 && !loadingTargets && (
              <div className="p-4 text-sm text-gray-500">No targets in this workspace yet.</div>
            )}
            {targets.map(t => {
              const scanned = !!(t.profile_data || t.last_scanned)
              const picked = pickedIds.includes(t.id)
              return (
                <button
                  type="button"
                  key={t.id}
                  onClick={() => scanned && togglePick(t.id)}
                  disabled={!scanned}
                  title={scanned ? '' : 'No scan data — run a scan first'}
                  className={`w-full flex items-center justify-between px-3 py-2 border-b border-[#1e1e2e] last:border-b-0 text-left text-sm transition-colors ${
                    picked
                      ? 'bg-[#3388ff]/15 text-white'
                      : scanned
                      ? 'hover:bg-white/5 text-gray-300'
                      : 'opacity-40 cursor-not-allowed text-gray-500'
                  }`}
                >
                  <span className="truncate">
                    <span className={`inline-block w-2 h-2 rounded-full mr-2 align-middle ${
                      picked ? 'bg-[#3388ff]' : scanned ? 'bg-[#00ff88]' : 'bg-gray-600'
                    }`} />
                    {t.email || t.id}
                  </span>
                  <span className="text-xs text-gray-500 ml-3 shrink-0">
                    {t.exposure_score != null && `E ${t.exposure_score}`}
                    {t.threat_score != null && ` · T ${t.threat_score}`}
                    {!scanned && ' · unscanned'}
                  </span>
                </button>
              )
            })}
          </div>
        </div>

        <div className="flex justify-end">
          <button
            type="button"
            onClick={handleSubmit}
            disabled={!formOk || submitting}
            className="flex items-center gap-2 bg-[#3388ff] hover:bg-[#3388ff]/90 disabled:opacity-40 disabled:cursor-not-allowed text-white font-semibold rounded-lg px-5 py-2.5 text-sm transition-colors"
          >
            {submitting ? <Loader2 className="w-4 h-4 animate-spin" /> : <Briefcase className="w-4 h-4" />}
            {submitting ? 'Generating…' : 'Generate case'}
          </button>
        </div>
      </section>

      {/* Past cases */}
      <section className="bg-[#12121a] border border-[#1e1e2e] rounded-xl p-5">
        <h2 className="text-sm font-semibold text-gray-300 uppercase tracking-wide mb-3">Past cases</h2>
        {loadingCases ? (
          <div className="text-sm text-gray-500">Loading…</div>
        ) : cases.length === 0 ? (
          <div className="text-sm text-gray-500">No cases yet.</div>
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-xs uppercase text-gray-500 border-b border-[#1e1e2e]">
                <th className="py-2 pr-3">Generated</th>
                <th className="py-2 pr-3">Tier</th>
                <th className="py-2 pr-3">Client</th>
                <th className="py-2 pr-3"># IDs</th>
                <th className="py-2 pr-3 text-right">Actions</th>
              </tr>
            </thead>
            <tbody>
              {cases.map(c => (
                <tr key={c.id} className="border-b border-[#1e1e2e] last:border-b-0">
                  <td className="py-2 pr-3 text-gray-400">{formatTimestamp(c.generated_at)}</td>
                  <td className="py-2 pr-3 font-mono text-xs text-[#3388ff]">{c.type?.replace('consult_', '') || '—'}</td>
                  <td className="py-2 pr-3 text-gray-300">{c.client_name || '—'}</td>
                  <td className="py-2 pr-3 text-gray-400">{c.target_count}</td>
                  <td className="py-2 pr-3 text-right">
                    <div className="flex items-center justify-end gap-2">
                      <button
                        type="button"
                        onClick={() => downloadConsultingCase(c.id).catch(err => setError(err.message))}
                        className="flex items-center gap-1 text-xs px-2.5 py-1.5 rounded border border-[#1e1e2e] text-[#00D4AA] hover:bg-[#00D4AA]/10 transition-colors"
                      >
                        <Download className="w-3 h-3" /> Download
                      </button>
                      <button
                        type="button"
                        onClick={() => setConfirmDelete(c.id)}
                        className="flex items-center gap-1 text-xs px-2.5 py-1.5 rounded border border-[#1e1e2e] text-[#ff2244] hover:bg-[#ff2244]/10 transition-colors"
                      >
                        <Trash2 className="w-3 h-3" /> Delete
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>

      {/* Delete confirmation modal */}
      {confirmDelete && (
        <div
          className="fixed inset-0 z-50 bg-black/60 flex items-center justify-center p-4"
          onClick={() => setConfirmDelete(null)}
        >
          <div
            className="bg-[#12121a] border border-[#1e1e2e] rounded-xl p-5 max-w-sm w-full"
            onClick={e => e.stopPropagation()}
          >
            <h3 className="text-base font-semibold text-white">Delete case?</h3>
            <p className="text-sm text-gray-500 mt-1">
              Row and Markdown file will be removed permanently.
            </p>
            <div className="flex justify-end gap-2 mt-4">
              <button
                type="button"
                onClick={() => setConfirmDelete(null)}
                className="text-xs px-3 py-1.5 rounded border border-[#1e1e2e] text-gray-300 hover:bg-white/5"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={() => handleDelete(confirmDelete)}
                className="text-xs px-3 py-1.5 rounded bg-[#ff2244] text-white hover:bg-[#ff2244]/90"
              >
                Delete
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
