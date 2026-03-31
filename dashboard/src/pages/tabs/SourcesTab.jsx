import { Globe } from 'lucide-react'

export default function SourcesTab({ sourcesData }) {
  const sources = sourcesData?.sources || []

  if (!sources.length) {
    return (
      <div className="bg-[#12121a] border border-[#1e1e2e] rounded-xl p-8 text-center text-gray-500 text-sm">
        No source data available. Run a scan to discover intelligence sources.
      </div>
    )
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-3 text-xs text-gray-400">
        <span><span className="text-white font-semibold">{sources.length}</span> sources</span>
        {sourcesData.overall_confidence > 0 && (
          <span>Overall confidence: <span className="text-white font-mono">{Math.round(sourcesData.overall_confidence * 100)}%</span></span>
        )}
        {sourcesData.cross_verified_count > 0 && (
          <span>{sourcesData.cross_verified_count} cross-verified</span>
        )}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-2">
        {sources.map(s => {
          const relColor = s.reliability >= 0.8 ? '#00ff88' : s.reliability >= 0.6 ? '#ffcc00' : '#ff8800'
          const pct = Math.round(s.reliability * 100)
          return (
            <div key={s.module} className="bg-[#12121a] border border-[#1e1e2e] rounded-lg p-3">
              <div className="flex items-center gap-2">
                <span className="text-xs font-mono font-medium truncate">{s.module}</span>
                <span className="text-[10px] px-1.5 py-0.5 rounded-full font-mono"
                  style={{ backgroundColor: relColor + '20', color: relColor }}>
                  {pct}%
                </span>
              </div>
              <div className="mt-1.5 h-1.5 rounded-full bg-[#0a0a0f] overflow-hidden">
                <div className="h-full rounded-full transition-all" style={{ width: `${pct}%`, backgroundColor: relColor }} />
              </div>
              <div className="flex gap-3 mt-1 text-[10px] text-gray-500">
                <span>{s.findings_count} findings</span>
                <span>{s.verified_count} verified</span>
                <span>avg {Math.round(s.avg_confidence * 100)}%</span>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
