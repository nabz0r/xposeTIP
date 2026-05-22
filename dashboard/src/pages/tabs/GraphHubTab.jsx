import IdentityGraph from '../../components/IdentityGraph'
import TimelineTab from './TimelineTab'

const SUB_TABS = [
  { key: 'graph',    label: 'Graph' },
  { key: 'timeline', label: 'Timeline' },
]

export default function GraphHubTab({ activeSub, setActiveSub, graphData, profile, findings }) {
  return (
    <div className="space-y-4">
      <div className="flex flex-wrap gap-2">
        {SUB_TABS.map(t => (
          <button key={t.key} onClick={() => setActiveSub(t.key)}
            className={`px-3 py-1.5 rounded-full text-xs font-medium transition-colors ${
              activeSub === t.key
                ? 'bg-[#00ff88]/20 text-[#00ff88] border border-[#00ff88]/40'
                : 'bg-[#12121a] text-gray-400 border border-[#1e1e2e] hover:text-white'
            }`}>
            {t.label}
          </button>
        ))}
      </div>
      {activeSub === 'graph' && <IdentityGraph data={graphData} personas={profile?.personas || []} />}
      {activeSub === 'timeline' && <TimelineTab profile={profile} findings={findings} />}
    </div>
  )
}
