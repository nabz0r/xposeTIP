import { useState } from 'react'
import { ChevronDown, ChevronRight } from 'lucide-react'

const severityColors = {
  critical: '#ff2244', high: '#ff8800', medium: '#ffcc00', low: '#3388ff', info: '#666688',
}

function groupByDate(findings) {
  const now = new Date()
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate())
  const yesterday = new Date(today); yesterday.setDate(yesterday.getDate() - 1)
  const weekAgo = new Date(today); weekAgo.setDate(weekAgo.getDate() - 7)

  const groups = { 'Today': [], 'Yesterday': [], 'This Week': [], 'Older': [] }

  const sorted = [...findings].sort((a, b) =>
    new Date(b.first_seen || b.created_at) - new Date(a.first_seen || a.created_at)
  )

  for (const f of sorted) {
    const d = new Date(f.first_seen || f.created_at)
    if (d >= today) groups['Today'].push(f)
    else if (d >= yesterday) groups['Yesterday'].push(f)
    else if (d >= weekAgo) groups['This Week'].push(f)
    else groups['Older'].push(f)
  }

  return Object.entries(groups).filter(([, items]) => items.length > 0)
}

export default function IOCTimeline({ findings }) {
  const [expanded, setExpanded] = useState(null)
  const groups = groupByDate(findings)

  if (!findings.length) {
    return (
      <div className="flex items-center justify-center h-64 text-gray-500">
        No findings to display in timeline.
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {groups.map(([label, items]) => (
        <div key={label}>
          <h3 className="text-xs font-semibold uppercase tracking-wider text-gray-500 mb-3">{label}</h3>
          <div className="relative ml-4 border-l border-[#1e1e2e]">
            {items.map(f => (
              <div key={f.id} className="relative pl-6 pb-4">
                {/* Severity dot */}
                <div className="absolute -left-[5px] top-1.5 w-2.5 h-2.5 rounded-full border-2 border-[#0a0a0f]"
                  style={{ backgroundColor: severityColors[f.severity] || '#666688' }} />

                <div
                  className="bg-[#12121a] border border-[#1e1e2e] rounded-lg p-3 cursor-pointer hover:bg-white/[0.03] transition-colors"
                  onClick={() => setExpanded(expanded === f.id ? null : f.id)}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <span className="inline-block text-xs font-medium px-2 py-0.5 rounded-full"
                        style={{ backgroundColor: (severityColors[f.severity] || '#666688') + '26', color: severityColors[f.severity] || '#666688' }}>
                        {f.severity}
                      </span>
                      <span className="text-sm">{f.title}</span>
                    </div>
                    <div className="flex items-center gap-3">
                      <span className="text-xs font-mono px-1.5 py-0.5 rounded bg-white/5 text-gray-400">{f.module}</span>
                      <span className="text-xs text-gray-500">
                        {f.first_seen ? new Date(f.first_seen).toLocaleDateString() : ''}
                      </span>
                      {expanded === f.id ? <ChevronDown className="w-3 h-3 text-gray-500" /> : <ChevronRight className="w-3 h-3 text-gray-500" />}
                    </div>
                  </div>

                  {expanded === f.id && (
                    <div className="mt-3 pt-3 border-t border-[#1e1e2e] text-sm text-gray-300">
                      {f.description}
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  )
}
