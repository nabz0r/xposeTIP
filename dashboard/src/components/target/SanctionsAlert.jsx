import { useMemo, useState } from 'react'
import { AlertTriangle, ChevronDown, ChevronUp, ExternalLink, Shield, Skull } from 'lucide-react'

const SEVERITY_CONFIG = {
  sanctions_match: { color: '#EF4444', bg: '#EF444410', border: '#EF444440', icon: Skull, label: 'Sanctions Match' },
  pep_match: { color: '#F59E0B', bg: '#F59E0B10', border: '#F59E0B40', icon: Shield, label: 'Politically Exposed Person' },
}

function TopicBadge({ topic }) {
  const colors = {
    sanction: { color: '#EF4444', bg: '#EF444415' },
    wanted: { color: '#EF4444', bg: '#EF444415' },
    crime: { color: '#EF4444', bg: '#EF444415' },
    'role.pep': { color: '#F59E0B', bg: '#F59E0B15' },
    'role.rca': { color: '#F59E0B', bg: '#F59E0B15' },
    debarment: { color: '#ff8800', bg: '#ff880015' },
    poi: { color: '#ff8800', bg: '#ff880015' },
  }
  const c = colors[topic] || { color: '#888', bg: '#88888815' }
  return (
    <span className="text-[10px] font-mono px-1.5 py-0.5 rounded uppercase tracking-wider"
      style={{ color: c.color, background: c.bg, border: `1px solid ${c.color}30` }}>
      {topic.replace('role.', '')}
    </span>
  )
}

export default function SanctionsAlert({ findings = [] }) {
  const [expanded, setExpanded] = useState(true)

  const sanctionsFindings = useMemo(() => {
    return findings.filter(f =>
      f.indicator_type === 'sanctions_match' || f.indicator_type === 'pep_match'
    )
  }, [findings])

  if (!sanctionsFindings.length) return null

  // Determine highest severity
  const hasSanctions = sanctionsFindings.some(f => f.indicator_type === 'sanctions_match')
  const config = hasSanctions ? SEVERITY_CONFIG.sanctions_match : SEVERITY_CONFIG.pep_match
  const Icon = config.icon

  // Group by type
  const sanctionMatches = sanctionsFindings.filter(f => f.indicator_type === 'sanctions_match')
  const pepMatches = sanctionsFindings.filter(f => f.indicator_type === 'pep_match')

  return (
    <div className="rounded-lg border mb-4" style={{ background: config.bg, borderColor: config.border }}>
      {/* Header — always visible */}
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-center justify-between px-4 py-3"
      >
        <div className="flex items-center gap-3">
          <Icon className="w-5 h-5" style={{ color: config.color }} />
          <div className="text-left">
            <span className="text-sm font-bold uppercase tracking-wider" style={{ color: config.color }}>
              {hasSanctions ? 'Sanctions Alert' : 'PEP Alert'}
            </span>
            <span className="text-xs text-gray-400 ml-3">
              {sanctionsFindings.length} potential match{sanctionsFindings.length > 1 ? 'es' : ''} found
            </span>
          </div>
        </div>
        {expanded
          ? <ChevronUp className="w-4 h-4 text-gray-500" />
          : <ChevronDown className="w-4 h-4 text-gray-500" />
        }
      </button>

      {/* Expanded content */}
      {expanded && (
        <div className="px-4 pb-4 space-y-3">
          {/* Sanctions matches */}
          {sanctionMatches.map((f, i) => (
            <div key={f.id || i} className="bg-[#0a0a12]/50 border border-[#1e1e2e] rounded-lg p-3">
              <div className="flex items-start justify-between gap-2">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="text-sm font-medium text-white">{f.data?.caption || f.title}</span>
                    {(f.data?.topics || []).map(t => <TopicBadge key={t} topic={t} />)}
                  </div>

                  {f.data?.dataset_labels?.length > 0 && (
                    <p className="text-xs text-gray-400 mt-1">
                      Listed on: {f.data.dataset_labels.join(', ')}
                    </p>
                  )}

                  {f.data?.listed_reason && (
                    <p className="text-xs text-gray-500 mt-1 line-clamp-2">{f.data.listed_reason}</p>
                  )}

                  {f.data?.charge && (
                    <p className="text-xs text-gray-500 mt-1 line-clamp-2">Charge: {f.data.charge}</p>
                  )}

                  <div className="flex items-center gap-3 mt-2 text-[10px] text-gray-600">
                    {f.data?.birth_date && <span>DOB: {f.data.birth_date}</span>}
                    {f.data?.nationality?.length > 0 && <span>Nationality: {f.data.nationality.join(', ')}</span>}
                    {f.data?.subtype && <span className="uppercase">{f.data.subtype.replace(/_/g, ' ')}</span>}
                  </div>
                </div>

                <div className="flex items-center gap-2 shrink-0">
                  <span className="text-xs font-mono px-1.5 py-0.5 rounded"
                    style={{ color: config.color, background: `${config.color}15`, border: `1px solid ${config.color}30` }}>
                    {Math.round((f.confidence || 0) * 100)}%
                  </span>
                  {f.url && (
                    <a href={f.url} target="_blank" rel="noopener noreferrer"
                      className="text-gray-500 hover:text-white transition-colors">
                      <ExternalLink className="w-3.5 h-3.5" />
                    </a>
                  )}
                </div>
              </div>
            </div>
          ))}

          {/* PEP matches */}
          {pepMatches.map((f, i) => (
            <div key={f.id || i} className="bg-[#0a0a12]/50 border border-[#F59E0B20] rounded-lg p-3">
              <div className="flex items-start justify-between gap-2">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 flex-wrap">
                    <Shield className="w-3.5 h-3.5 text-[#F59E0B]" />
                    <span className="text-sm font-medium text-white">{f.data?.caption || f.title}</span>
                    {(f.data?.topics || []).map(t => <TopicBadge key={t} topic={t} />)}
                  </div>

                  {f.data?.dataset_labels?.length > 0 && (
                    <p className="text-xs text-gray-400 mt-1">
                      Source: {f.data.dataset_labels.join(', ')}
                    </p>
                  )}

                  {f.data?.nationality?.length > 0 && (
                    <p className="text-xs text-gray-500 mt-1">
                      Country: {f.data.nationality.join(', ').toUpperCase()}
                    </p>
                  )}

                  <p className="text-[10px] text-[#F59E0B]/60 mt-2">
                    PEP status requires enhanced due diligence under AML regulations
                  </p>
                </div>

                <div className="flex items-center gap-2 shrink-0">
                  <span className="text-xs font-mono px-1.5 py-0.5 rounded"
                    style={{ color: '#F59E0B', background: '#F59E0B15', border: '1px solid #F59E0B30' }}>
                    {Math.round((f.confidence || 0) * 100)}%
                  </span>
                  {f.url && (
                    <a href={f.url} target="_blank" rel="noopener noreferrer"
                      className="text-gray-500 hover:text-white transition-colors">
                      <ExternalLink className="w-3.5 h-3.5" />
                    </a>
                  )}
                </div>
              </div>
            </div>
          ))}

          {/* MANDATORY confidence disclaimer */}
          <div className="bg-[#1e1e2e]/50 rounded-lg p-3 border border-[#2a2a3e]">
            <div className="flex items-start gap-2">
              <AlertTriangle className="w-3.5 h-3.5 text-gray-500 shrink-0 mt-0.5" />
              <p className="text-[10px] text-gray-500 leading-relaxed">
                These results are potential matches based on name similarity. A match does NOT confirm
                the target is the listed person. Always verify through official channels before taking action.
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
