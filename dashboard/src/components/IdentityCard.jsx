const COUNTRY_NAMES = {
  US: 'United States', GB: 'United Kingdom', FR: 'France', DE: 'Germany', ES: 'Spain',
  IT: 'Italy', NL: 'Netherlands', BE: 'Belgium', CH: 'Switzerland', AT: 'Austria',
  SE: 'Sweden', NO: 'Norway', DK: 'Denmark', FI: 'Finland', PL: 'Poland',
  PT: 'Portugal', IE: 'Ireland', CZ: 'Czech Republic', RO: 'Romania', HU: 'Hungary',
  EG: 'Egypt', DZ: 'Algeria', MA: 'Morocco', TN: 'Tunisia', LY: 'Libya',
  SA: 'Saudi Arabia', AE: 'UAE', TR: 'Turkey', IL: 'Israel', LB: 'Lebanon',
  IN: 'India', PK: 'Pakistan', BD: 'Bangladesh', CN: 'China', JP: 'Japan',
  KR: 'South Korea', ID: 'Indonesia', PH: 'Philippines', TH: 'Thailand', VN: 'Vietnam',
  BR: 'Brazil', MX: 'Mexico', AR: 'Argentina', CO: 'Colombia', CL: 'Chile',
  CA: 'Canada', AU: 'Australia', NZ: 'New Zealand', ZA: 'South Africa', NG: 'Nigeria',
  RU: 'Russia', UA: 'Ukraine', LU: 'Luxembourg', SG: 'Singapore', MY: 'Malaysia',
  IQ: 'Iraq', SY: 'Syria', JO: 'Jordan', PS: 'Palestine', KW: 'Kuwait',
}

const countryFlag = (code) => {
  if (!code || code.length !== 2) return '🌍'
  return String.fromCodePoint(
    ...[...code.toUpperCase()].map(c => c.charCodeAt(0) + 127397)
  )
}

export default function IdentityCard({ profile }) {
  const est = profile?.identity_estimation
  const avatars = profile?.avatars || []

  // Don't render if no identity estimation data at all
  if (!est || (!est.gender && !est.age && (!est.nationalities || est.nationalities.length === 0))) {
    return null
  }

  const genderIcon = est.gender === 'male' ? '♂' : est.gender === 'female' ? '♀' : '⚧'
  const genderColor = est.gender === 'male' ? '#3388ff' : est.gender === 'female' ? '#ff66aa' : '#ffcc00'

  return (
    <div className="bg-[#12121a] border border-[#1e1e2e] rounded-xl p-5">
      <h3 className="text-xs font-semibold uppercase tracking-wider text-gray-500 mb-4">Identity Estimation</h3>

      {/* Photo strip */}
      {avatars.length > 0 && (
        <div className="flex gap-2 mb-5">
          {avatars.slice(0, 6).map((a, i) => (
            <div key={i} className="group relative">
              <img src={a.url} alt="" className="w-14 h-14 rounded-full border-2 border-[#1e1e2e] object-cover transition-all group-hover:border-[#00ff88]/50 group-hover:shadow-[0_0_12px_rgba(0,255,136,0.15)]" />
              <div className="absolute -bottom-1 left-1/2 -translate-x-1/2 text-[8px] bg-[#0a0a0f] px-1 rounded text-gray-500 opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap">
                {a.source}
              </div>
            </div>
          ))}
          {avatars.length > 6 && (
            <div className="w-14 h-14 rounded-full bg-[#1e1e2e] flex items-center justify-center text-xs text-gray-500 font-mono">
              +{avatars.length - 6}
            </div>
          )}
        </div>
      )}

      <div className="space-y-4">
        {/* Gender */}
        {est.gender && (
          <div className="flex items-center gap-3">
            <span className="text-xl" style={{ color: genderColor }}>{genderIcon}</span>
            <div className="flex-1">
              <div className="flex items-center justify-between mb-1">
                <span className="text-sm font-medium capitalize">{est.gender}</span>
                <span className="text-xs font-mono text-gray-400">{est.gender_probability != null ? `${Math.round(est.gender_probability * 100)}%` : ''}</span>
              </div>
              {est.gender_probability != null && (
                <div className="h-1.5 bg-[#0a0a0f] rounded-full overflow-hidden">
                  <div className="h-full rounded-full transition-all duration-700" style={{ width: `${est.gender_probability * 100}%`, backgroundColor: '#00ff88' }} />
                </div>
              )}
            </div>
          </div>
        )}

        {/* Age */}
        {est.age && (
          <div className="flex items-center gap-3">
            <span className="text-xl text-gray-400">~</span>
            <div>
              <span className="text-sm font-medium font-mono">{est.age} years old</span>
              {est.age_sample_count > 0 && (
                <span className="text-[10px] text-gray-500 ml-2">({est.age_sample_count.toLocaleString()} samples)</span>
              )}
            </div>
          </div>
        )}

        {/* Nationalities */}
        {est.nationalities && est.nationalities.length > 0 && (
          <div className="space-y-2">
            {est.nationalities.map((n, i) => (
              <div key={i} className={`flex items-center gap-3${n.probability < 0.05 ? ' opacity-50' : ''}`}>
                <span className="text-xl">{countryFlag(n.country_code)}</span>
                <div className="flex-1">
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-sm">{COUNTRY_NAMES[n.country_code] || n.country_code}</span>
                    <span className="text-xs font-mono text-gray-400">{Math.round(n.probability * 100)}%</span>
                  </div>
                  <div className="h-1.5 bg-[#0a0a0f] rounded-full overflow-hidden">
                    <div className="h-full rounded-full transition-all duration-700" style={{ width: `${n.probability * 100}%`, backgroundColor: '#00ff88' }} />
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Footer */}
      <div className="mt-4 pt-3 border-t border-[#1e1e2e]">
        <p className="text-[10px] text-gray-600">
          Statistical estimation · {est.age_sample_count > 0 ? `${est.age_sample_count.toLocaleString()}+ samples · ` : ''}confidence increases with more sources
        </p>
      </div>
    </div>
  )
}
