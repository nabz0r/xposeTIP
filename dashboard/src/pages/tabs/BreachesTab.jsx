import { Shield } from 'lucide-react'

const severityColors = {
  critical: '#ff2244', high: '#ff8800', medium: '#ffcc00', low: '#3388ff', info: '#666688',
}

export default function BreachesTab({ breachFindings }) {
  if (!breachFindings.length) {
    return (
      <div className="bg-[#12121a] border border-[#1e1e2e] rounded-xl p-8 text-center text-gray-500 text-sm">
        <Shield className="w-10 h-10 text-gray-700 mx-auto mb-3" />
        <h3 className="text-gray-400 text-sm mb-1">No breaches detected</h3>
        <p className="text-gray-600 text-xs">This email was not found in any known data breaches.</p>
      </div>
    )
  }

  const hasPasswords = breachFindings.some(f => {
    const dc = f.data?.DataClasses || f.data?.data_classes || []
    return dc.some(d => d.toLowerCase().includes('password'))
  })

  return (
    <div className="space-y-4">
      {/* Summary */}
      <div className="flex items-center gap-4 text-xs text-gray-400">
        <span><span className="text-white font-semibold">{breachFindings.length}</span> breach{breachFindings.length !== 1 ? 'es' : ''}</span>
        {hasPasswords && (
          <span className="text-red-400 font-semibold">Credentials leaked</span>
        )}
      </div>

      {/* Breach cards */}
      <div className="space-y-3">
        {breachFindings.map(f => {
          const d = f.data || {}
          const name = d.Name || d.breach_name || f.title
          const date = d.BreachDate || d.date || ''
          const dataClasses = d.DataClasses || d.data_classes || []
          const count = d.PwnCount || d.records || ''
          const hasPass = dataClasses.some(dc => dc.toLowerCase().includes('password'))

          return (
            <div key={f.id} className={`bg-[#12121a] border rounded-lg p-4 ${hasPass ? 'border-[#ff2244]/30' : 'border-[#1e1e2e]'}`}>
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                  <Shield className="w-4 h-4 text-[#ff2244]" />
                  <span className="text-sm font-semibold">{name}</span>
                  <span className="inline-block text-[10px] font-medium px-1.5 py-0.5 rounded-full"
                    style={{ backgroundColor: (severityColors[f.severity] || '#666688') + '26', color: severityColors[f.severity] }}>
                    {f.severity}
                  </span>
                </div>
                {date && <span className="text-xs text-gray-500">{date}</span>}
              </div>

              <p className="text-xs text-gray-400 mb-2">{f.description}</p>

              {dataClasses.length > 0 && (
                <div className="flex flex-wrap gap-1.5 mb-2">
                  {dataClasses.map(dc => (
                    <span key={dc} className={`text-[10px] px-2 py-0.5 rounded ${
                      dc.toLowerCase().includes('password') ? 'bg-[#ff2244]/15 text-[#ff2244]' :
                      dc.toLowerCase().includes('email') ? 'bg-[#ff8800]/15 text-[#ff8800]' :
                      'bg-[#1e1e2e] text-gray-400'
                    }`}>{dc}</span>
                  ))}
                </div>
              )}

              <div className="flex items-center gap-4 text-[10px] text-gray-600">
                {count && <span>{typeof count === 'number' ? count.toLocaleString() : count} records</span>}
                <span>Module: {f.module}</span>
                {hasPass && <span className="text-red-400 font-semibold">Password exposed</span>}
              </div>

              {hasPass && (
                <div className="mt-2 p-2 bg-[#ff2244]/5 rounded text-[10px] text-gray-400">
                  <span className="text-red-400 font-semibold">Action needed:</span> Change this password immediately. If reused on other services, change those too. Enable 2FA.
                </div>
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}
