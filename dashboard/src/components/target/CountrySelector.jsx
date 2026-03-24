import { useState, useRef, useEffect } from 'react'
import { Check, X, ChevronDown } from 'lucide-react'
import { updateTargetCountry } from '../../lib/api'

const FLAG = (code) => {
  if (!code) return ''
  return String.fromCodePoint(...[...code.toUpperCase()].map(c => 0x1F1E6 + c.charCodeAt(0) - 65))
}

// ISO 3166-1 alpha-2 subset (most common)
const COUNTRIES = [
  { code: 'AF', name: 'Afghanistan' }, { code: 'AL', name: 'Albania' }, { code: 'DZ', name: 'Algeria' },
  { code: 'AR', name: 'Argentina' }, { code: 'AM', name: 'Armenia' }, { code: 'AU', name: 'Australia' },
  { code: 'AT', name: 'Austria' }, { code: 'AZ', name: 'Azerbaijan' }, { code: 'BH', name: 'Bahrain' },
  { code: 'BD', name: 'Bangladesh' }, { code: 'BY', name: 'Belarus' }, { code: 'BE', name: 'Belgium' },
  { code: 'BA', name: 'Bosnia' }, { code: 'BR', name: 'Brazil' }, { code: 'BG', name: 'Bulgaria' },
  { code: 'CA', name: 'Canada' }, { code: 'CL', name: 'Chile' }, { code: 'CN', name: 'China' },
  { code: 'CO', name: 'Colombia' }, { code: 'HR', name: 'Croatia' }, { code: 'CU', name: 'Cuba' },
  { code: 'CY', name: 'Cyprus' }, { code: 'CZ', name: 'Czechia' }, { code: 'DK', name: 'Denmark' },
  { code: 'EC', name: 'Ecuador' }, { code: 'EG', name: 'Egypt' }, { code: 'EE', name: 'Estonia' },
  { code: 'ET', name: 'Ethiopia' }, { code: 'FI', name: 'Finland' }, { code: 'FR', name: 'France' },
  { code: 'GE', name: 'Georgia' }, { code: 'DE', name: 'Germany' }, { code: 'GH', name: 'Ghana' },
  { code: 'GR', name: 'Greece' }, { code: 'HK', name: 'Hong Kong' }, { code: 'HU', name: 'Hungary' },
  { code: 'IS', name: 'Iceland' }, { code: 'IN', name: 'India' }, { code: 'ID', name: 'Indonesia' },
  { code: 'IR', name: 'Iran' }, { code: 'IQ', name: 'Iraq' }, { code: 'IE', name: 'Ireland' },
  { code: 'IL', name: 'Israel' }, { code: 'IT', name: 'Italy' }, { code: 'JP', name: 'Japan' },
  { code: 'JO', name: 'Jordan' }, { code: 'KZ', name: 'Kazakhstan' }, { code: 'KE', name: 'Kenya' },
  { code: 'KR', name: 'South Korea' }, { code: 'KW', name: 'Kuwait' }, { code: 'LV', name: 'Latvia' },
  { code: 'LB', name: 'Lebanon' }, { code: 'LY', name: 'Libya' }, { code: 'LI', name: 'Liechtenstein' },
  { code: 'LT', name: 'Lithuania' }, { code: 'LU', name: 'Luxembourg' }, { code: 'MY', name: 'Malaysia' },
  { code: 'MT', name: 'Malta' }, { code: 'MX', name: 'Mexico' }, { code: 'MD', name: 'Moldova' },
  { code: 'MC', name: 'Monaco' }, { code: 'ME', name: 'Montenegro' }, { code: 'MA', name: 'Morocco' },
  { code: 'NL', name: 'Netherlands' }, { code: 'NZ', name: 'New Zealand' }, { code: 'NG', name: 'Nigeria' },
  { code: 'MK', name: 'North Macedonia' }, { code: 'NO', name: 'Norway' }, { code: 'OM', name: 'Oman' },
  { code: 'PK', name: 'Pakistan' }, { code: 'PA', name: 'Panama' }, { code: 'PE', name: 'Peru' },
  { code: 'PH', name: 'Philippines' }, { code: 'PL', name: 'Poland' }, { code: 'PT', name: 'Portugal' },
  { code: 'QA', name: 'Qatar' }, { code: 'RO', name: 'Romania' }, { code: 'RU', name: 'Russia' },
  { code: 'SA', name: 'Saudi Arabia' }, { code: 'RS', name: 'Serbia' }, { code: 'SG', name: 'Singapore' },
  { code: 'SK', name: 'Slovakia' }, { code: 'SI', name: 'Slovenia' }, { code: 'ZA', name: 'South Africa' },
  { code: 'ES', name: 'Spain' }, { code: 'SE', name: 'Sweden' }, { code: 'CH', name: 'Switzerland' },
  { code: 'SY', name: 'Syria' }, { code: 'TW', name: 'Taiwan' }, { code: 'TH', name: 'Thailand' },
  { code: 'TN', name: 'Tunisia' }, { code: 'TR', name: 'Turkey' }, { code: 'UA', name: 'Ukraine' },
  { code: 'AE', name: 'UAE' }, { code: 'GB', name: 'United Kingdom' }, { code: 'US', name: 'United States' },
  { code: 'UY', name: 'Uruguay' }, { code: 'UZ', name: 'Uzbekistan' }, { code: 'VE', name: 'Venezuela' },
  { code: 'VN', name: 'Vietnam' },
]

export default function CountrySelector({ targetId, currentCode, onUpdate }) {
  const [editing, setEditing] = useState(false)
  const [search, setSearch] = useState('')
  const [saving, setSaving] = useState(false)
  const [saved, setSaved] = useState(false)
  const dropdownRef = useRef(null)
  const inputRef = useRef(null)

  useEffect(() => {
    if (editing && inputRef.current) inputRef.current.focus()
  }, [editing])

  useEffect(() => {
    if (!editing) return
    const handleClickOutside = (e) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target)) {
        setEditing(false)
        setSearch('')
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [editing])

  const handleSelect = async (code) => {
    setSaving(true)
    setEditing(false)
    setSearch('')
    try {
      await updateTargetCountry(targetId, code)
      onUpdate?.(code)
      setSaved(true)
      setTimeout(() => setSaved(false), 1500)
    } catch (e) {
      console.error('Failed to update country:', e)
    }
    setSaving(false)
  }

  const filtered = COUNTRIES.filter(c =>
    c.name.toLowerCase().includes(search.toLowerCase()) ||
    c.code.toLowerCase().includes(search.toLowerCase())
  )

  if (editing) {
    return (
      <div ref={dropdownRef} className="relative inline-block">
        <input
          ref={inputRef}
          type="text"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search country..."
          className="bg-[#1e1e2e] border border-[#3388ff]/50 rounded px-2 py-0.5 text-xs text-white w-36 focus:outline-none focus:border-[#3388ff]"
        />
        <div className="absolute z-50 mt-1 bg-[#12121a] border border-[#1e1e2e] rounded-lg shadow-xl max-h-48 overflow-y-auto w-48">
          <button
            onClick={() => handleSelect(null)}
            className="w-full text-left px-3 py-1.5 text-xs text-gray-400 hover:bg-[#1e1e2e] border-b border-[#1e1e2e]"
          >
            <X className="w-3 h-3 inline mr-1" />
            Clear country
          </button>
          {filtered.map(c => (
            <button
              key={c.code}
              onClick={() => handleSelect(c.code)}
              className={`w-full text-left px-3 py-1.5 text-xs hover:bg-[#1e1e2e] flex items-center gap-2 ${
                c.code === currentCode ? 'text-[#00ff88]' : 'text-gray-300'
              }`}
            >
              <span>{FLAG(c.code)}</span>
              <span>{c.name}</span>
              <span className="text-gray-600 font-mono ml-auto">{c.code}</span>
            </button>
          ))}
          {filtered.length === 0 && (
            <div className="px-3 py-2 text-xs text-gray-500">No match</div>
          )}
        </div>
      </div>
    )
  }

  return (
    <button
      onClick={() => setEditing(true)}
      disabled={saving}
      className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-xs hover:bg-[#1e1e2e] transition-colors group"
      title="Click to change country"
    >
      {saving ? (
        <span className="text-gray-500">...</span>
      ) : saved ? (
        <Check className="w-3 h-3 text-[#00ff88]" />
      ) : currentCode ? (
        <>
          <span>{FLAG(currentCode)}</span>
          <span className="text-gray-400 font-mono">{currentCode}</span>
          <ChevronDown className="w-3 h-3 text-gray-600 opacity-0 group-hover:opacity-100 transition-opacity" />
        </>
      ) : (
        <>
          <span className="text-gray-600">No country</span>
          <ChevronDown className="w-3 h-3 text-gray-600 opacity-0 group-hover:opacity-100 transition-opacity" />
        </>
      )}
    </button>
  )
}
