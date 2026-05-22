const SERVICE_TIERS = [
  {
    level: 'I',
    name: 'Read',
    price: 'Free',
    play: null,
    description: 'See your own behavioral fingerprint. Every axis, every claim, every source attribution. The asymmetry of information is the first thing BFP corrects.',
  },
  {
    level: 'II',
    name: 'Guidance',
    price: 'Free',
    play: null,
    description: 'Receive remediation guidance per finding. Concrete, prioritized steps the subject can take themselves. Education first.',
  },
  {
    level: 'III',
    name: 'Monitoring',
    price: 'Paid',
    play: 'Play 3a',
    description: 'Continuous tracking. Alerts on fingerprint changes — new exposures, leaked credentials, account compromises. Subscription-based.',
  },
  {
    level: 'IV',
    name: 'Managed remediation',
    price: 'Paid',
    play: 'Play 3b',
    description: 'xposeTIP acts on the subject\'s behalf — opt-out requests, deletion requests, takedown filings. One-shot engagement for high-stakes cleanups.',
  },
]

export default function BFPSubjectLayer() {
  return (
    <div className="max-w-5xl mx-auto px-6">
      <div className="text-center mb-16">
        <div className="text-xs font-mono text-[#00ff88]/70 uppercase tracking-wider mb-3">Subject Layer</div>
        <h2 className="text-3xl md:text-4xl font-bold mb-4 font-['Instrument_Sans',sans-serif]">
          The subject is a first-class participant
        </h2>
        <p className="text-sm text-gray-500 max-w-2xl mx-auto leading-relaxed">
          Not an object of investigation, not a data point being sold.
          The subject reads, follows guidance, optionally subscribes to monitoring, and retains a legal safety valve.
        </p>
      </div>

      {/* Four service tiers */}
      <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-10">
        {SERVICE_TIERS.map((t) => {
          const isPaid = t.price === 'Paid'
          return (
            <div
              key={t.level}
              className="p-5 bg-[#13131c] border border-[#1e1e2e] rounded-lg flex flex-col"
            >
              <div className="flex items-center justify-between mb-3">
                <span className="text-xs font-mono text-gray-500">Level {t.level}</span>
                <span
                  className={`text-xs font-mono px-2 py-0.5 rounded ${
                    isPaid
                      ? 'bg-[#00ff88]/10 text-[#00ff88] border border-[#00ff88]/30'
                      : 'bg-gray-800 text-gray-400 border border-gray-700'
                  }`}
                >
                  {t.price}
                </span>
              </div>
              <h3 className="text-base font-bold text-white mb-1 font-['Instrument_Sans',sans-serif]">
                {t.name}
              </h3>
              {t.play && (
                <div className="text-xs font-mono text-[#00ff88]/60 mb-3">{t.play}</div>
              )}
              <p className="text-xs text-gray-400 leading-relaxed mt-auto">{t.description}</p>
            </div>
          )
        })}
      </div>

      {/* Takedown — separate, emphasized as different category */}
      <div className="p-6 bg-[#13131c] border border-[#aa66ff]/30 rounded-lg">
        <div className="flex items-start gap-4">
          <div className="shrink-0">
            <div className="w-10 h-10 rounded-full bg-[#aa66ff]/10 border border-[#aa66ff]/30 flex items-center justify-center text-[#aa66ff] font-mono text-sm">
              ⏻
            </div>
          </div>
          <div className="flex-1">
            <div className="flex items-center gap-3 mb-2">
              <h3 className="text-base font-bold text-white font-['Instrument_Sans',sans-serif]">
                Takedown
              </h3>
              <span className="text-xs font-mono text-[#aa66ff]">Legal safety valve</span>
            </div>
            <p className="text-sm text-gray-400 leading-relaxed">
              Not a service tier — a regulatory mechanism. Removal from the corpus on presentation of a legally recognized basis:
              court order, GDPR Article 8 child-data claim, expunged criminal record, witness-protection enrollment.
              The default is transparency-empowerment; this is the exception, not the rule.
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
