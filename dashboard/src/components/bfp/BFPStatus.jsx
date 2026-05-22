const STATS = [
  { label: 'Version', value: 'v1.3.4', mono: true },
  { label: 'Sprints shipped', value: '163+', mono: true },
  { label: 'Active scrapers', value: '110 / 127', mono: true },
  { label: 'Fingerprint axes', value: '11', mono: true },
  { label: 'License', value: 'AGPL-3.0', mono: true },
  { label: 'Crypto suite', value: 'NIST 2024 PQC', mono: true },
]

export default function BFPStatus() {
  return (
    <div className="max-w-5xl mx-auto px-6">
      <div className="text-center mb-12">
        <div className="text-xs font-mono text-[#00ff88]/70 uppercase tracking-wider mb-3">Status</div>
        <h2 className="text-3xl md:text-4xl font-bold mb-4 font-['Instrument_Sans',sans-serif]">
          Reference implementation, live
        </h2>
        <div className="inline-flex items-center gap-2 text-xs font-mono text-gray-400 mb-2">
          <span className="w-1.5 h-1.5 bg-[#00ff88] rounded-full animate-pulse" />
          xposeTIP — May 2026
        </div>
      </div>

      <div className="grid sm:grid-cols-2 md:grid-cols-3 gap-3 mb-10">
        {STATS.map((s) => (
          <div
            key={s.label}
            className="p-5 bg-[#13131c] border border-[#1e1e2e] rounded-lg"
          >
            <div className="text-xs font-mono text-gray-500 uppercase tracking-wider mb-2">
              {s.label}
            </div>
            <div className={`text-xl font-bold text-white ${s.mono ? "font-mono" : "font-['Instrument_Sans',sans-serif]"}`}>
              {s.value}
            </div>
          </div>
        ))}
      </div>

      <div className="text-center text-sm text-gray-500">
        Reference implementation is open-source.{' '}
        <a
          href="https://github.com/nabz0r/xposeTIP"
          target="_blank"
          rel="noopener noreferrer"
          className="text-[#00ff88] hover:underline"
        >
          View on GitHub →
        </a>
      </div>
    </div>
  )
}
