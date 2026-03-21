import { useEffect, useState } from 'react'
import { Plus, Code, Play, Download, Upload, X, Trash2, ToggleLeft, ToggleRight, ChevronDown, ChevronRight } from 'lucide-react'
import { getScrapers, getScraper, createScraper, updateScraper, deleteScraper, testScraper, toggleScraper, exportScraper, importScraper } from '../lib/api'

const CATEGORIES = ['social', 'breach', 'metadata', 'people_search', 'identity', 'archive', 'gaming']
const INPUT_TYPES = ['email', 'username', 'domain', 'url', 'ip', 'first_name']
const RULE_TYPES = ['json_key', 'regex', 'jsonpath']
const SEVERITIES = ['info', 'low', 'medium', 'high', 'critical']
const TRANSFORMS = ['', 'lowercase', 'strip_html', 'parse_int', 'strip']

const statusColor = (s) => s === 'working' ? '#00ff88' : s === 'broken' ? '#ff2244' : s === 'rate_limited' ? '#ff8800' : '#666688'

export default function Scrapers() {
  const [scrapers, setScrapers] = useState([])
  const [selected, setSelected] = useState(null)
  const [editing, setEditing] = useState(null)
  const [testInput, setTestInput] = useState('')
  const [testResult, setTestResult] = useState(null)
  const [testing, setTesting] = useState(false)
  const [saving, setSaving] = useState(false)
  const [showImport, setShowImport] = useState(false)
  const [importJson, setImportJson] = useState('')
  const [catFilter, setCatFilter] = useState('all')

  useEffect(() => { loadScrapers() }, [])

  async function loadScrapers() {
    try {
      const data = await getScrapers()
      setScrapers(data.items || [])
    } catch {}
  }

  function openEditor(scraper) {
    setSelected(scraper.id)
    setEditing({ ...scraper })
    setTestResult(null)
    setTestInput('')
  }

  function newScraper() {
    setSelected('new')
    setEditing({
      name: '', display_name: '', description: '', category: 'social',
      url_template: '', method: 'GET', headers: {}, input_type: 'username',
      input_transform: '', extraction_rules: [],
      finding_title_template: '', finding_category: 'social_account',
      finding_severity: 'low', success_indicator: '', not_found_indicators: [],
      rate_limit_requests: 1, rate_limit_window: 2, notes: '',
    })
    setTestResult(null)
  }

  async function handleSave() {
    if (!editing) return
    setSaving(true)
    try {
      if (selected === 'new') {
        await createScraper(editing)
      } else {
        await updateScraper(selected, editing)
      }
      await loadScrapers()
      setSelected(null)
      setEditing(null)
    } catch (err) { alert(err.message) }
    finally { setSaving(false) }
  }

  async function handleTest() {
    if (!selected || selected === 'new' || !testInput) return
    setTesting(true)
    setTestResult(null)
    try {
      const result = await testScraper(selected, testInput)
      setTestResult(result)
      loadScrapers()
    } catch (err) { setTestResult({ error: err.message }) }
    finally { setTesting(false) }
  }

  async function handleToggle(id) {
    try {
      await toggleScraper(id)
      loadScrapers()
    } catch {}
  }

  async function handleDelete(id) {
    if (!confirm('Delete this scraper?')) return
    try {
      await deleteScraper(id)
      if (selected === id) { setSelected(null); setEditing(null) }
      loadScrapers()
    } catch (err) { alert(err.message) }
  }

  async function handleExport(id) {
    try {
      const data = await exportScraper(id)
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `scraper-${data.xpose_scraper_v1?.name || 'export'}.json`
      a.click()
      URL.revokeObjectURL(url)
    } catch (err) { alert(err.message) }
  }

  async function handleImport() {
    try {
      const data = JSON.parse(importJson)
      await importScraper(data)
      setShowImport(false)
      setImportJson('')
      loadScrapers()
    } catch (err) { alert(err.message) }
  }

  function addRule() {
    setEditing(prev => ({
      ...prev,
      extraction_rules: [...(prev.extraction_rules || []), { field: '', type: 'json_key', pattern: '', group: 1, default: null, transform: '' }]
    }))
  }

  function updateRule(idx, key, value) {
    setEditing(prev => {
      const rules = [...prev.extraction_rules]
      rules[idx] = { ...rules[idx], [key]: value }
      return { ...prev, extraction_rules: rules }
    })
  }

  function removeRule(idx) {
    setEditing(prev => ({
      ...prev,
      extraction_rules: prev.extraction_rules.filter((_, i) => i !== idx)
    }))
  }

  const filtered = catFilter === 'all' ? scrapers : scrapers.filter(s => s.category === catFilter)

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold flex items-center gap-2">
          <Code className="w-6 h-6 text-[#00ff88]" /> Scrapers
          <span className="text-sm text-gray-500 font-normal ml-2">{scrapers.length}</span>
        </h1>
        <div className="flex gap-2">
          <button onClick={() => setShowImport(true)} className="flex items-center gap-2 bg-[#12121a] border border-[#1e1e2e] text-gray-300 rounded-lg px-3 py-2 text-sm hover:border-[#00ff88]/50">
            <Upload className="w-4 h-4" /> Import
          </button>
          <button onClick={newScraper} className="flex items-center gap-2 bg-[#00ff88] text-black font-semibold rounded-lg px-4 py-2 text-sm hover:bg-[#00ff88]/90">
            <Plus className="w-4 h-4" /> New Scraper
          </button>
        </div>
      </div>

      {/* Category filter */}
      <div className="flex gap-2">
        {['all', ...CATEGORIES].map(c => (
          <button key={c} onClick={() => setCatFilter(c)}
            className={`text-xs px-3 py-1.5 rounded-full capitalize ${catFilter === c ? 'bg-[#00ff88]/20 text-[#00ff88]' : 'bg-[#12121a] text-gray-400 hover:text-white'}`}>
            {c}
          </button>
        ))}
      </div>

      <div className="flex gap-4">
        {/* List */}
        <div className="w-80 shrink-0 space-y-1">
          {filtered.map(s => (
            <div key={s.id} onClick={() => openEditor(s)}
              className={`bg-[#12121a] border rounded-lg p-3 cursor-pointer transition-colors ${
                selected === s.id ? 'border-[#00ff88]/50' : 'border-[#1e1e2e] hover:border-gray-600'
              }`}>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2 min-w-0">
                  <div className="w-2 h-2 rounded-full shrink-0" style={{ backgroundColor: statusColor(s.last_test_status) }} />
                  <span className="text-sm font-medium truncate">{s.display_name || s.name}</span>
                </div>
                <div className="flex items-center gap-1 shrink-0">
                  <button onClick={e => { e.stopPropagation(); handleToggle(s.id) }} className="text-gray-500 hover:text-[#00ff88]">
                    {s.enabled ? <ToggleRight className="w-4 h-4 text-[#00ff88]" /> : <ToggleLeft className="w-4 h-4" />}
                  </button>
                  <button onClick={e => { e.stopPropagation(); handleExport(s.id) }} className="text-gray-500 hover:text-[#3388ff]">
                    <Download className="w-3.5 h-3.5" />
                  </button>
                  <button onClick={e => { e.stopPropagation(); handleDelete(s.id) }} className="text-gray-500 hover:text-[#ff2244]">
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>
              <div className="flex items-center gap-2 mt-1">
                <span className="text-[10px] px-1.5 py-0.5 rounded bg-[#1e1e2e] text-gray-500 capitalize">{s.category}</span>
                <span className="text-[10px] text-gray-600">{s.input_type}</span>
                {s.last_test_status && (
                  <span className="text-[10px] font-mono" style={{ color: statusColor(s.last_test_status) }}>{s.last_test_status}</span>
                )}
              </div>
            </div>
          ))}
          {filtered.length === 0 && (
            <div className="text-center text-sm text-gray-500 py-8">No scrapers found</div>
          )}
        </div>

        {/* Editor */}
        {editing && (
          <div className="flex-1 bg-[#12121a] border border-[#1e1e2e] rounded-xl p-5 space-y-4 overflow-y-auto max-h-[calc(100vh-200px)]">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-semibold">{selected === 'new' ? 'New Scraper' : editing.display_name || editing.name}</h2>
              <div className="flex gap-2">
                {selected !== 'new' && (
                  <button onClick={handleTest} disabled={testing || !testInput}
                    className="flex items-center gap-1 bg-[#3388ff]/20 text-[#3388ff] rounded-lg px-3 py-1.5 text-xs hover:bg-[#3388ff]/30 disabled:opacity-50">
                    <Play className="w-3 h-3" /> {testing ? 'Testing...' : 'Test'}
                  </button>
                )}
                <button onClick={handleSave} disabled={saving}
                  className="flex items-center gap-1 bg-[#00ff88] text-black font-semibold rounded-lg px-3 py-1.5 text-xs hover:bg-[#00ff88]/90 disabled:opacity-50">
                  {saving ? 'Saving...' : 'Save'}
                </button>
                <button onClick={() => { setSelected(null); setEditing(null) }} className="text-gray-500 hover:text-white">
                  <X className="w-4 h-4" />
                </button>
              </div>
            </div>

            {/* Basic fields */}
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="text-[10px] text-gray-500 uppercase">Name (unique ID)</label>
                <input value={editing.name || ''} onChange={e => setEditing(p => ({ ...p, name: e.target.value }))}
                  className="w-full bg-[#0a0a0f] border border-[#1e1e2e] rounded px-3 py-2 text-sm font-mono focus:outline-none focus:border-[#00ff88]/50" />
              </div>
              <div>
                <label className="text-[10px] text-gray-500 uppercase">Display Name</label>
                <input value={editing.display_name || ''} onChange={e => setEditing(p => ({ ...p, display_name: e.target.value }))}
                  className="w-full bg-[#0a0a0f] border border-[#1e1e2e] rounded px-3 py-2 text-sm focus:outline-none focus:border-[#00ff88]/50" />
              </div>
            </div>

            <div>
              <label className="text-[10px] text-gray-500 uppercase">URL Template</label>
              <input value={editing.url_template || ''} onChange={e => setEditing(p => ({ ...p, url_template: e.target.value }))}
                placeholder="https://api.example.com/users/{username}"
                className="w-full bg-[#0a0a0f] border border-[#1e1e2e] rounded px-3 py-2 text-sm font-mono focus:outline-none focus:border-[#00ff88]/50" />
            </div>

            <div className="grid grid-cols-4 gap-3">
              <div>
                <label className="text-[10px] text-gray-500 uppercase">Input Type</label>
                <select value={editing.input_type} onChange={e => setEditing(p => ({ ...p, input_type: e.target.value }))}
                  className="w-full bg-[#0a0a0f] border border-[#1e1e2e] rounded px-3 py-2 text-sm focus:outline-none">
                  {INPUT_TYPES.map(t => <option key={t} value={t}>{t}</option>)}
                </select>
              </div>
              <div>
                <label className="text-[10px] text-gray-500 uppercase">Method</label>
                <select value={editing.method} onChange={e => setEditing(p => ({ ...p, method: e.target.value }))}
                  className="w-full bg-[#0a0a0f] border border-[#1e1e2e] rounded px-3 py-2 text-sm focus:outline-none">
                  <option value="GET">GET</option>
                  <option value="POST">POST</option>
                </select>
              </div>
              <div>
                <label className="text-[10px] text-gray-500 uppercase">Category</label>
                <select value={editing.category || 'social'} onChange={e => setEditing(p => ({ ...p, category: e.target.value }))}
                  className="w-full bg-[#0a0a0f] border border-[#1e1e2e] rounded px-3 py-2 text-sm focus:outline-none">
                  {CATEGORIES.map(c => <option key={c} value={c}>{c}</option>)}
                </select>
              </div>
              <div>
                <label className="text-[10px] text-gray-500 uppercase">Severity</label>
                <select value={editing.finding_severity || 'low'} onChange={e => setEditing(p => ({ ...p, finding_severity: e.target.value }))}
                  className="w-full bg-[#0a0a0f] border border-[#1e1e2e] rounded px-3 py-2 text-sm focus:outline-none">
                  {SEVERITIES.map(s => <option key={s} value={s}>{s}</option>)}
                </select>
              </div>
            </div>

            <div>
              <label className="text-[10px] text-gray-500 uppercase">Headers (JSON)</label>
              <input value={JSON.stringify(editing.headers || {})} onChange={e => {
                try { setEditing(p => ({ ...p, headers: JSON.parse(e.target.value) })) } catch {}
              }} className="w-full bg-[#0a0a0f] border border-[#1e1e2e] rounded px-3 py-2 text-sm font-mono focus:outline-none focus:border-[#00ff88]/50" />
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="text-[10px] text-gray-500 uppercase">Success Indicator (regex)</label>
                <input value={editing.success_indicator || ''} onChange={e => setEditing(p => ({ ...p, success_indicator: e.target.value }))}
                  className="w-full bg-[#0a0a0f] border border-[#1e1e2e] rounded px-3 py-2 text-sm font-mono focus:outline-none focus:border-[#00ff88]/50" />
              </div>
              <div>
                <label className="text-[10px] text-gray-500 uppercase">Finding Title Template</label>
                <input value={editing.finding_title_template || ''} onChange={e => setEditing(p => ({ ...p, finding_title_template: e.target.value }))}
                  placeholder="{service}: {display_name}"
                  className="w-full bg-[#0a0a0f] border border-[#1e1e2e] rounded px-3 py-2 text-sm font-mono focus:outline-none focus:border-[#00ff88]/50" />
              </div>
            </div>

            {/* Extraction Rules */}
            <div>
              <div className="flex items-center justify-between mb-2">
                <label className="text-[10px] text-gray-500 uppercase">Extraction Rules ({(editing.extraction_rules || []).length})</label>
                <button onClick={addRule} className="text-[10px] text-[#00ff88] hover:underline flex items-center gap-1">
                  <Plus className="w-3 h-3" /> Add Rule
                </button>
              </div>
              <div className="space-y-2">
                {(editing.extraction_rules || []).map((rule, i) => (
                  <div key={i} className="flex items-center gap-2 bg-[#0a0a0f] rounded p-2">
                    <input value={rule.field || ''} onChange={e => updateRule(i, 'field', e.target.value)}
                      placeholder="field" className="w-28 bg-transparent border border-[#1e1e2e] rounded px-2 py-1 text-xs font-mono focus:outline-none focus:border-[#00ff88]/50" />
                    <select value={rule.type || 'json_key'} onChange={e => updateRule(i, 'type', e.target.value)}
                      className="bg-transparent border border-[#1e1e2e] rounded px-2 py-1 text-xs focus:outline-none">
                      {RULE_TYPES.map(t => <option key={t} value={t}>{t}</option>)}
                    </select>
                    <input value={rule.pattern || ''} onChange={e => updateRule(i, 'pattern', e.target.value)}
                      placeholder="pattern" className="flex-1 bg-transparent border border-[#1e1e2e] rounded px-2 py-1 text-xs font-mono focus:outline-none focus:border-[#00ff88]/50" />
                    <select value={rule.transform || ''} onChange={e => updateRule(i, 'transform', e.target.value)}
                      className="bg-transparent border border-[#1e1e2e] rounded px-2 py-1 text-xs focus:outline-none w-20">
                      {TRANSFORMS.map(t => <option key={t} value={t}>{t || 'none'}</option>)}
                    </select>
                    <button onClick={() => removeRule(i)} className="text-gray-500 hover:text-[#ff2244] shrink-0">
                      <X className="w-3.5 h-3.5" />
                    </button>
                  </div>
                ))}
              </div>
            </div>

            {/* Rate limit */}
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="text-[10px] text-gray-500 uppercase">Rate Limit (requests)</label>
                <input type="number" value={editing.rate_limit_requests || 1} onChange={e => setEditing(p => ({ ...p, rate_limit_requests: parseInt(e.target.value) || 1 }))}
                  className="w-full bg-[#0a0a0f] border border-[#1e1e2e] rounded px-3 py-2 text-sm font-mono focus:outline-none" />
              </div>
              <div>
                <label className="text-[10px] text-gray-500 uppercase">Window (seconds)</label>
                <input type="number" value={editing.rate_limit_window || 2} onChange={e => setEditing(p => ({ ...p, rate_limit_window: parseInt(e.target.value) || 2 }))}
                  className="w-full bg-[#0a0a0f] border border-[#1e1e2e] rounded px-3 py-2 text-sm font-mono focus:outline-none" />
              </div>
            </div>

            {/* Test section */}
            {selected !== 'new' && (
              <div className="border-t border-[#1e1e2e] pt-4">
                <label className="text-[10px] text-gray-500 uppercase mb-2 block">Test Scraper</label>
                <div className="flex gap-2 mb-3">
                  <input value={testInput} onChange={e => setTestInput(e.target.value)}
                    placeholder="Enter test input (email, username...)"
                    className="flex-1 bg-[#0a0a0f] border border-[#1e1e2e] rounded px-3 py-2 text-sm font-mono focus:outline-none focus:border-[#00ff88]/50" />
                  <button onClick={handleTest} disabled={testing || !testInput}
                    className="bg-[#3388ff]/20 text-[#3388ff] rounded px-4 py-2 text-sm hover:bg-[#3388ff]/30 disabled:opacity-50">
                    {testing ? 'Running...' : 'Run Test'}
                  </button>
                </div>

                {testResult && (
                  <div className="space-y-3">
                    <div className="flex items-center gap-2">
                      <div className={`w-2 h-2 rounded-full ${testResult.found ? 'bg-[#00ff88]' : testResult.error ? 'bg-[#ff2244]' : 'bg-[#666688]'}`} />
                      <span className={`text-sm font-medium ${testResult.found ? 'text-[#00ff88]' : testResult.error ? 'text-[#ff2244]' : 'text-gray-400'}`}>
                        {testResult.found ? 'Found' : testResult.error ? `Error: ${testResult.error}` : 'Not Found'}
                      </span>
                      {testResult.status_code && <span className="text-xs text-gray-500">HTTP {testResult.status_code}</span>}
                    </div>

                    {testResult.extracted && Object.keys(testResult.extracted).length > 0 && (
                      <div>
                        <label className="text-[10px] text-gray-500 uppercase mb-1 block">Extracted Data</label>
                        <div className="bg-[#0a0a0f] rounded p-3 space-y-1">
                          {Object.entries(testResult.extracted).map(([k, v]) => (
                            <div key={k} className="flex gap-2 text-xs">
                              <span className="text-gray-500 w-28 shrink-0 font-mono">{k}:</span>
                              <span className="text-[#00ff88] font-mono break-all">{typeof v === 'object' ? JSON.stringify(v) : String(v)}</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {testResult.raw_html && (
                      <div>
                        <label className="text-[10px] text-gray-500 uppercase mb-1 block">Raw Response (first 500 chars)</label>
                        <pre className="bg-[#0a0a0f] rounded p-3 text-[10px] font-mono text-gray-400 overflow-x-auto max-h-32 whitespace-pre-wrap">
                          {testResult.raw_html.substring(0, 500)}
                        </pre>
                      </div>
                    )}
                  </div>
                )}
              </div>
            )}
          </div>
        )}

        {!editing && (
          <div className="flex-1 flex items-center justify-center text-gray-600 text-sm">
            Select a scraper to edit or create a new one
          </div>
        )}
      </div>

      {/* Import modal */}
      {showImport && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50" onClick={() => setShowImport(false)}>
          <div className="bg-[#12121a] border border-[#1e1e2e] rounded-xl p-6 w-full max-w-lg" onClick={e => e.stopPropagation()}>
            <h2 className="text-lg font-semibold mb-4">Import Scraper</h2>
            <textarea value={importJson} onChange={e => setImportJson(e.target.value)} rows={12}
              placeholder='Paste scraper JSON here...'
              className="w-full bg-[#0a0a0f] border border-[#1e1e2e] rounded-lg px-3 py-2 text-sm font-mono focus:outline-none focus:border-[#00ff88]/50 resize-none mb-4" />
            <div className="flex justify-end gap-2">
              <button onClick={() => setShowImport(false)} className="px-4 py-2 text-sm text-gray-400 hover:text-white">Cancel</button>
              <button onClick={handleImport} className="bg-[#00ff88] text-black font-semibold rounded-lg px-4 py-2 text-sm hover:bg-[#00ff88]/90">Import</button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
