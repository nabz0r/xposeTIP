// Finding classification helpers — single source of truth.
// Used by RiskSignalsBlock (S119) + Findings tab preset filter (S120).
// Keep in sync with seed_scrapers.py (api/scrapers/* names).

export const PHONE_SCRAPERS = [
  'numverify_phone',
  'veriphone_phone',
  'carrier_lookup',
  'google_phone_dork',
]

export const CRYPTO_SCRAPERS = [
  'blockchain_info_btc',
  'blockchair_wallet',
  'chainabuse_lookup',
]

export const isPhoneSignal = (f) => PHONE_SCRAPERS.includes(f?.data?.scraper)
export const isCryptoSignal = (f) => CRYPTO_SCRAPERS.includes(f?.data?.scraper)
export const isLegalSignal = (f) => f?.indicator_type === 'legal_record'

export const PRESET_FILTERS = {
  all: null,
  phone: isPhoneSignal,
  crypto: isCryptoSignal,
  legal: isLegalSignal,
}

export const applyPreset = (findings, preset) => {
  const fn = PRESET_FILTERS[preset]
  if (!fn) return findings
  return findings.filter(fn)
}
