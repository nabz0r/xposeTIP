// Finding classification helpers — single source of truth.
// Used by RiskSignalsBlock (S119) + Findings tab preset filter (S120).
// Keep in sync with seed_scrapers.py + api/scrapers/* names.

// CRITICAL: scraper name lives in `f.data.scraper` for findings emitted by
// scraper_engine, but in the `f.module` column for findings emitted by
// secondary_identifier_enricher (A1.6 path) and api/scrapers (PASS2 path).
// Read both with a fallback (S192 Bug 1 fix).
const getScraperName = (f) => f?.data?.scraper || f?.module

export const PHONE_SCRAPERS = [
  'numverify_phone',
  'veriphone_phone',
  'google_phone_dork',
  // S192 Bug 3: 'carrier_lookup' removed — dead reference, no such scraper in seed or api/scrapers/
]

export const CRYPTO_SCRAPERS = [
  // Tier 1 BTC (S183 + pre-existing)
  'blockchain_info_btc',
  'blockchair_wallet',
  'mempool_space_btc',
  // Tier 1 EVM blockscouts (S183)
  'blockscout_eth',
  'blockscout_optimism',
  'blockscout_base',
  'blockscout_gnosis',
  // ENS + scam DBs (S183)
  'ensideas_resolve',
  'chainabuse_check',   // S192 Bug 2 fix: was incorrectly 'chainabuse_lookup'
  'cryptoscamdb_check',
  // Tier 2 keyed (S183) — forward-compatible for when keys are configured
  'arbiscan_eth_balance',
  'etherscan_full',
  'bscscan_address',
  'polygonscan_address',
  'solscan_address',
]

export const isPhoneSignal = (f) => PHONE_SCRAPERS.includes(getScraperName(f))
export const isCryptoSignal = (f) => CRYPTO_SCRAPERS.includes(getScraperName(f))
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
