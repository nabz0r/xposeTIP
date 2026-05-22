import FindingsTab from './FindingsTab'
import PublicExposureTab from '../../components/target/PublicExposureTab'
import BreachesTab from './BreachesTab'
import UsernameTab from './UsernameTab'
import PhotosTab from './PhotosTab'
import LocationMap from '../../components/LocationMap'
import DiscoveredTab from './DiscoveredTab'

const SUB_TABS = [
  { key: 'all',        label: 'All' },
  { key: 'exposure',   label: 'Public exposure' },
  { key: 'breaches',   label: 'Breaches' },
  { key: 'usernames',  label: 'Usernames' },
  { key: 'photos',     label: 'Photos' },
  { key: 'locations',  label: 'Locations' },
  { key: 'discovered', label: 'Discovered' },
]

export default function FindingsHubTab({
  activeSub, setActiveSub,
  // Findings list props
  target, findings, filteredFindings, expanded, setExpanded,
  sevFilter, setSevFilter, modFilter, setModFilter,
  statusFilter, setStatusFilter, presetFilter, setPresetFilter,
  findingsLimit, setFindingsLimit, uniqueModules, load, patchFinding, targetId,
  // Sub-view props
  profile, socialFindings, breachFindings, geoFindings, graphData,
}) {
  // Per-category counts — sourced to match the prior top-tab badge logic
  // (TargetDetail pre-S157 lines 430-440) so visible numbers don't shift.
  const exposureCount = findings.filter(f =>
    f.category === 'public_exposure' ||
    f.category === 'compliance' ||
    f.category === 'corporate' ||
    f.indicator_type === 'media_mention' ||
    f.indicator_type === 'sanctions_match' ||
    f.indicator_type === 'pep_match' ||
    f.indicator_type === 'corporate_officer'
  ).length
  const usernameCount = new Set(
    findings
      .filter(f => f.indicator_type === 'username' && f.indicator_value)
      .map(f => f.indicator_value.toLowerCase())
  ).size

  const counts = {
    all: findings.length,
    exposure: exposureCount,
    breaches: breachFindings?.length || 0,
    usernames: usernameCount,
    photos: (profile?.avatars?.length || 0),
    locations: (profile?.user_locations?.length || 0) + (geoFindings?.length || 0),
    discovered: null,  // computed inside DiscoveredTab via API call — hide count
  }

  return (
    <div className="space-y-4">
      {/* Sub-pill nav */}
      <div className="flex flex-wrap gap-2">
        {SUB_TABS.map(t => (
          <button key={t.key} onClick={() => setActiveSub(t.key)}
            className={`px-3 py-1.5 rounded-full text-xs font-medium transition-colors ${
              activeSub === t.key
                ? 'bg-[#00ff88]/20 text-[#00ff88] border border-[#00ff88]/40'
                : 'bg-[#12121a] text-gray-400 border border-[#1e1e2e] hover:text-white'
            }`}>
            {t.label}
            {counts[t.key] != null && counts[t.key] > 0 && (
              <span className="ml-1.5 font-mono opacity-70">{counts[t.key]}</span>
            )}
          </button>
        ))}
      </div>

      {/* Sub-content */}
      {activeSub === 'all' && (
        <FindingsTab
          target={target} findings={findings} filteredFindings={filteredFindings}
          expanded={expanded} setExpanded={setExpanded}
          sevFilter={sevFilter} setSevFilter={setSevFilter}
          modFilter={modFilter} setModFilter={setModFilter}
          statusFilter={statusFilter} setStatusFilter={setStatusFilter}
          presetFilter={presetFilter} setPresetFilter={setPresetFilter}
          findingsLimit={findingsLimit} setFindingsLimit={setFindingsLimit}
          uniqueModules={uniqueModules} load={load} patchFinding={patchFinding}
          targetId={targetId} onRefresh={load}
        />
      )}
      {activeSub === 'exposure' && <PublicExposureTab findings={findings} profile={profile} />}
      {activeSub === 'breaches' && <BreachesTab breachFindings={breachFindings} />}
      {activeSub === 'usernames' && (
        <UsernameTab findings={findings} graphData={graphData} targetId={targetId} onRefresh={load} />
      )}
      {activeSub === 'photos' && <PhotosTab profile={profile} target={target} />}
      {activeSub === 'locations' && (
        <LocationMap findings={findings} userLocations={profile?.user_locations} countryCode={target?.country_code} />
      )}
      {activeSub === 'discovered' && <DiscoveredTab targetId={targetId} targetStatus={target?.status} />}
    </div>
  )
}
