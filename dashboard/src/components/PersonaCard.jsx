const PERSONA_COLORS = [
  '#00ff88', '#3388ff', '#ff8800', '#aa55ff', '#ffcc00', '#ff4466', '#00ddcc',
]

export default function PersonaCard({ personas }) {
  if (!personas || personas.length === 0) return null

  return (
    <div className="bg-[#12121a] border border-[#1e1e2e] rounded-xl p-5">
      <h3 className="text-xs font-semibold uppercase tracking-wider text-gray-500 mb-4">
        Digital Personas ({personas.length})
      </h3>
      <div className="space-y-3">
        {personas.map((p, i) => (
          <div key={p.id}
            className={`rounded-lg p-4 bg-[#0a0a0f] border-l-4 ${
              p.is_primary ? 'border-l-[#00ff88]' : 'border-l-[#1e1e2e]'
            }`}
          >
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-2">
                <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: PERSONA_COLORS[i % PERSONA_COLORS.length] }} />
                <span className="font-mono text-sm font-semibold text-gray-200">@{p.label}</span>
                {p.is_primary && (
                  <span className="text-[10px] font-mono px-1.5 py-0.5 rounded-full bg-[#00ff88]/10 text-[#00ff88]">Primary</span>
                )}
                {!p.is_primary && (
                  <span className="text-[10px] font-mono px-1.5 py-0.5 rounded-full bg-[#1e1e2e] text-gray-500">Secondary</span>
                )}
              </div>
              <span className="text-[10px] font-mono text-gray-500">{Math.round(p.confidence * 100)}% confidence</span>
            </div>

            {/* Platform pills */}
            <div className="flex flex-wrap gap-1.5 mb-2">
              {p.platforms.map(platform => (
                <span key={platform}
                  className="inline-flex items-center px-2 py-0.5 text-[10px] font-mono bg-[#1e1e2e] rounded text-gray-400">
                  {platform}
                </span>
              ))}
            </div>

            {/* Username variants */}
            {p.usernames.length > 1 && (
              <div className="text-[10px] text-gray-500 mb-1">
                Variants: {p.usernames.map(u => `@${u}`).join(', ')}
              </div>
            )}

            {/* Risk indicators */}
            {p.risk_indicators.length > 0 && (
              <div className="space-y-0.5 mt-2">
                {p.risk_indicators.map((r, ri) => (
                  <div key={ri} className="text-[10px] text-[#ff8800] flex items-center gap-1">
                    <span>⚠</span>
                    <span>{r.replace(/_/g, ' ')}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}
