import React, { useMemo } from 'react'
import { Phone, Wallet, Scale, ChevronRight } from 'lucide-react'
import { PHONE_SCRAPERS, CRYPTO_SCRAPERS } from '../lib/findingFilters'

const SEVERITY_COLORS = {
  critical: '#ff2244',
  high: '#ff8800',
  medium: '#ffcc00',
  low: '#3388ff',
  info: '#666688',
}

const severityColor = (s) => SEVERITY_COLORS[s] || '#666688'

const truncate = (s, n = 20) => {
  if (!s) return ''
  const str = String(s)
  if (str.length <= n) return str
  return str.slice(0, Math.floor(n / 2)) + '…' + str.slice(-Math.floor(n / 2))
}

function SignalColumn({ icon: Icon, label, accent, findings, onViewAll, renderItem }) {
  if (!findings.length) return null
  const topItems = findings.slice(0, 2)
  return (
    <div className="bg-[#0a0a0f] border border-[#1e1e2e] rounded-lg p-4 flex flex-col">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <Icon className="w-4 h-4" style={{ color: accent }} />
          <span className="text-xs font-semibold uppercase tracking-wider text-gray-400">{label}</span>
        </div>
        <span
          className="text-xs font-mono font-bold px-2 py-0.5 rounded-full"
          style={{ backgroundColor: accent + '26', color: accent }}
        >
          {findings.length}
        </span>
      </div>
      <div className="space-y-1.5 flex-1">
        {topItems.map((f, i) => (
          <div key={i} className="text-[11px] text-gray-300 leading-tight">
            {renderItem(f)}
          </div>
        ))}
      </div>
      {findings.length > topItems.length && (
        <button
          onClick={onViewAll}
          className="mt-3 text-[10px] text-gray-500 hover:text-gray-300 flex items-center gap-0.5 self-start"
        >
          View all {findings.length} <ChevronRight className="w-3 h-3" />
        </button>
      )}
    </div>
  )
}

export default function RiskSignalsBlock({ findings, onViewAll }) {
  const { phoneFindings, cryptoFindings, legalFindings } = useMemo(() => {
    const phone = []
    const crypto = []
    const legal = []
    for (const f of findings || []) {
      const scraper = f.data?.scraper
      if (scraper && PHONE_SCRAPERS.includes(scraper)) {
        phone.push(f)
      } else if (scraper && CRYPTO_SCRAPERS.includes(scraper)) {
        crypto.push(f)
      } else if (f.indicator_type === 'legal_record') {
        legal.push(f)
      }
    }
    return { phoneFindings: phone, cryptoFindings: crypto, legalFindings: legal }
  }, [findings])

  const total = phoneFindings.length + cryptoFindings.length + legalFindings.length
  if (total === 0) return null

  return (
    <div className="bg-[#12121a] border border-[#1e1e2e] rounded-xl p-5">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-xs font-semibold uppercase tracking-wider text-gray-500">
          Risk Signals
        </h3>
        <span className="text-[10px] text-gray-600">{total} signal{total !== 1 ? 's' : ''} detected</span>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
        <SignalColumn
          icon={Phone}
          label="Phone"
          accent="#3388ff"
          findings={phoneFindings}
          onViewAll={() => onViewAll && onViewAll('phone')}
          renderItem={(f) => {
            const data = f.data || {}
            const number = data.intl_format || data.phone || f.indicator_value || ''
            const carrier = data.carrier || ''
            const lineType = data.line_type || data.phone_type || ''
            return (
              <div className="flex items-center justify-between gap-2">
                <span className="font-mono truncate">{truncate(number, 18)}</span>
                <span className="text-gray-500 shrink-0">
                  {carrier || lineType || ''}
                </span>
              </div>
            )
          }}
        />
        <SignalColumn
          icon={Wallet}
          label="Crypto"
          accent="#aa66ff"
          findings={cryptoFindings}
          onViewAll={() => onViewAll && onViewAll('crypto')}
          renderItem={(f) => {
            const data = f.data || {}
            const address = f.indicator_value || data.address || ''
            const txCount = data.tx_count
            const chain = data.scraper === 'blockchair_wallet' ? 'multi-chain' :
                          data.scraper === 'chainabuse_lookup' ? 'reported' : 'BTC'
            return (
              <div className="flex items-center justify-between gap-2">
                <span className="font-mono truncate">{truncate(address, 16)}</span>
                <span className="text-gray-500 shrink-0">
                  {txCount != null ? `${txCount} tx` : chain}
                </span>
              </div>
            )
          }}
        />
        <SignalColumn
          icon={Scale}
          label="Legal"
          accent="#ff8800"
          findings={legalFindings}
          onViewAll={() => onViewAll && onViewAll('legal')}
          renderItem={(f) => {
            const data = f.data || {}
            const jurisdiction = data.jurisdiction || 'unknown'
            const title = f.title || data.case_name || 'Court record'
            return (
              <div className="flex items-center justify-between gap-2">
                <span className="truncate" title={title}>{truncate(title, 28)}</span>
                <span
                  className="font-mono text-[9px] px-1 py-0.5 rounded shrink-0"
                  style={{ backgroundColor: severityColor(f.severity) + '26', color: severityColor(f.severity) }}
                >
                  {jurisdiction}
                </span>
              </div>
            )
          }}
        />
      </div>
    </div>
  )
}
