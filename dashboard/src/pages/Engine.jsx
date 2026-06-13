import { Link } from 'react-router-dom'
import Section from '../components/shared/Section'
import { SOURCE_COUNT } from '../components/landing/constants'
import EngineFlowDiagram from '../components/engine/EngineFlowDiagram'

// S301b — /doc/engine. The "ultra-precise" pathway: how one email seed rotates
// through the producer systems (a) + infra rotation (b) and resolves into a
// scored identity. Full-raw: literal SCANNER_REGISTRY + env-var key inventory.
// Everything below is verified from the real code (tip 06cc749) — nothing invented.

// ── §1 producer dispatch — literal SCANNER_REGISTRY (28) ──
const REGISTRY = `Layer 1 — email / social / identity
  email_validator  → layer1.email_validator:EmailValidatorScanner
  holehe           → layer1.holehe_scanner:HoleheScanner
  hibp             → layer1.hibp_scanner:HIBPScanner
  sherlock         → layer1.sherlock_scanner:SherlockScanner
  gravatar         → layer1.gravatar_scanner:GravatarScanner
  social_enricher  → layer1.social_enricher:SocialEnricherScanner
  google_profile   → layer1.google_scanner:GoogleScanner
  emailrep         → layer1.emailrep_scanner:EmailRepScanner
  epieos           → layer1.epieos_scanner:EpieosScanner
  fullcontact      → layer1.fullcontact_scanner:FullContactScanner
  github_deep      → layer1.github_scanner:GitHubDeepScanner
  gpg_keys         → layer1.gpg_scanner:GpgKeysScanner
  username_hunter  → layer1.username_scanner:UsernameScannerPlugin
  reverse_image    → layer1.reverse_image_scanner:ReverseImageScanner

Layer 1 — scraper engines
  scraper_engine      → layer1.scraper_scanner:ScraperScanner   (fans out 179 URL-templates)
  name_scraper_engine → layer1.name_scraper_scanner:NameScraperScanner

Layer 2 — network / premium (key-gated)
  whois_lookup   → layer2.whois_scanner:WhoisScanner
  maxmind_geo    → layer2.maxmind_scanner:MaxmindScanner
  geoip          → layer2.geoip_scanner:GeoIPScanner
  leaked_domains → layer2.leaked_scanner:LeakedScanner
  dns_deep       → layer2.dns_scanner:DNSDeepScanner
  virustotal     → layer2.virustotal_scanner:VirusTotalScanner
  shodan         → layer2.shodan_scanner:ShodanScanner
  intelx         → layer2.intelx_scanner:IntelXScanner
  hunter         → layer2.hunter_scanner:HunterScanner
  dehashed       → layer2.dehashed_scanner:DehashedScanner

Layer 3 — SaaS OAuth
  google_audit    → layer3.google_connector:GoogleConnector
  microsoft_audit → layer3.microsoft_connector:MicrosoftConnector`

// ── §2 the pipeline ladder — exact A1→B9 (18 stages, no fabricated B10-B12) ──
const LADDER = [
  ['A1', 'Cross-verify findings across sources (confidence boost)'],
  ['A1.5', 'Extract secondary identifiers (phone, crypto) from findings'],
  ['A1.6', 'Enrich secondary identifiers via dedicated scrapers'],
  ['A2', 'Pass 1.5 — username expansion (re-scan discovered usernames)'],
  ['A3', 'Early profile aggregation (bootstrap primary_name)'],
  ['A3.5', 'Name-input scrapers (after A3, before A4)'],
  ['A4', 'Pass 2 — public exposure enrichment (name-based scrapers)'],
  ['B0', 'Email deliverability check (frontend banner tag)'],
  ['B1', 'Build identity graph (sees Pass 1 + 1.5 + 2)'],
  ['B2', 'Propagate confidence — PageRank (damping 0.85, 20 iter, conv 0.001)'],
  ['B3', 'Build graph_context (unified intelligence layer)'],
  ['B4', 'Compute exposure score (with graph_context)'],
  ['B5', 'Aggregate profile data (FINAL — overwrites early profile)'],
  ['B6', 'Bio rejection (Telegram slogans / noise)'],
  ['B7', 'Blacklist check on display_name'],
  ['B8', 'Store quick_teaser (freemium landing flow)'],
  ['B9', 'Identity enrichment (re-query with discovered name)'],
]

// ── §3 infra rotation — literal env-var key inventory (provider → key → module). Values never shown. ──
const KEYS = [
  ['HIBP_API_KEY', 'Have I Been Pwned', 'hibp'],
  ['MAXMIND_LICENSE', 'MaxMind GeoLite2', 'maxmind_geo'],
  ['FULLCONTACT_API_KEY', 'FullContact', 'fullcontact'],
  ['GITHUB_TOKEN', 'GitHub Personal Token', 'github_deep'],
  ['SHODAN_API_KEY', 'Shodan', 'shodan'],
  ['VIRUSTOTAL_API_KEY', 'VirusTotal', 'virustotal'],
  ['INTELX_API_KEY', 'Intelligence X', 'intelx'],
  ['DEHASHED_API_KEY', 'Dehashed', 'dehashed'],
  ['HUNTER_API_KEY', 'Hunter.io', 'hunter'],
  ['PIMEYES_API_KEY', 'PimEyes', 'reverse_image'],
  ['PROXYCURL_API_KEY', 'ProxyCurl (LinkedIn)', 'proxycurl_linkedin'],
  ['ROCKETREACH_API_KEY', 'RocketReach', 'email→LinkedIn'],
  ['GOOGLE_CSE_API_KEY', 'Google Custom Search', 'LinkedIn discovery'],
  ['gnews_api_key', 'GNews.io', 'press'],
  ['opencorporates_api_key', 'OpenCorporates', 'corporate'],
  ['NUMVERIFY_API_KEY', 'Numverify', 'phone (scraper-engine)'],
  ['ABSTRACTAPI_PHONE_KEY', 'AbstractAPI Phone', 'phone (scraper-engine)'],
  ['GOOGLE_CLIENT_ID / SECRET', 'Google OAuth', 'google_audit'],
  ['MICROSOFT_CLIENT_ID / SECRET', 'Microsoft OAuth', 'microsoft_audit'],
]

// ── §4 scoring — severity → confidence map ──
const SEVERITY = [
  ['critical', '0.85'], ['high', '0.75'], ['medium', '0.65'], ['low', '0.50'], ['info', '0.40'],
]

function ProducerCard({ count, unit, title, body, accent }) {
  return (
    <div className="bg-[#12121a] border border-[#1e1e2e] rounded-xl p-5 flex flex-col">
      <div className="flex items-baseline gap-1.5 mb-3">
        <span className="text-3xl font-mono font-bold" style={{ color: accent }}>{count}</span>
        <span className="text-xs text-gray-500 font-mono">{unit}</span>
      </div>
      <div className="text-sm font-semibold text-white mb-1">{title}</div>
      <div className="text-sm text-gray-400 leading-relaxed">{body}</div>
    </div>
  )
}

export default function Engine() {
  return (
    <div className="pb-20">
      {/* Hero */}
      <Section className="py-20">
        <div className="max-w-5xl mx-auto px-6 text-center">
          <h1 className="text-4xl md:text-5xl font-bold mb-4 font-['Instrument_Sans',sans-serif]">
            The <span className="text-[#00ff88]">engine</span>
          </h1>
          <p className="text-lg text-gray-400 max-w-2xl mx-auto">
            How one email rotates through every producer and resolves into a scored identity.
            The exact pathway — dispatch, multi-pass, scoring — read straight from the code.
          </p>
        </div>
        <EngineFlowDiagram />
      </Section>

      {/* §1 — Producer rotation */}
      <Section className="py-16 bg-[#0d0d14]">
        <div className="max-w-5xl mx-auto px-6">
          <h2 className="text-2xl font-bold mb-2 font-['Instrument_Sans',sans-serif]">1 · Producer rotation</h2>
          <p className="text-gray-400 max-w-3xl mb-8 leading-relaxed">
            The engine doesn&apos;t run a list — it <span className="text-white">rotates</span>. A single seed fans
            out across three producer systems as a Celery <span className="font-mono text-[#3388ff]">chord</span>
            {' '}(parallel, not sequential); the <span className="font-mono">finalize_scan</span> callback fires once
            every module completes. Each pass widens the surface the next pass searches.
          </p>
          <div className="grid md:grid-cols-3 gap-4 mb-10">
            <ProducerCard count="28" unit="scanners" accent="#00ff88"
              title="SCANNER_REGISTRY" body="Python scanner classes dispatched in the chord — Layer-1 email/social/identity, Layer-2 network/premium (key-gated), Layer-3 SaaS OAuth." />
            <ProducerCard count={SOURCE_COUNT} unit="sources" accent="#3388ff"
              title="URL-template scrapers" body="Fanned out internally by scraper_engine → ScraperScanner. DB-defined templates (seed_scrapers.py), not code-per-source." />
            <ProducerCard count="12" unit="api-modules" accent="#aa66ff"
              title="public_exposure_enricher" body="Name-based enrichment connectors (press, corporate registries, LinkedIn discovery) that run in Pass 2 — after the name resolves." />
          </div>

          <h3 className="text-sm font-mono text-gray-500 uppercase tracking-wider mb-2">Multi-pass model</h3>
          <p className="text-gray-400 max-w-3xl mb-6 leading-relaxed">
            <span className="font-mono text-white">Pass 1</span> = the chord (28 scanners parallel, raw findings) →
            {' '}<span className="font-mono text-white">Pass 1.5</span> = derive secondary identifiers + re-scan
            discovered usernames →
            {' '}<span className="font-mono text-white">Pass 2</span> = name-based scrapers, dispatched only after
            the primary name is resolved. <span className="font-mono">name_scraper_engine</span> is special-cased to
            run <span className="text-white">after</span> profile aggregation — not in the initial chord.
          </p>

          <h3 className="text-sm font-mono text-gray-500 uppercase tracking-wider mb-2">SCANNER_REGISTRY — verbatim</h3>
          <pre className="bg-[#0a0a0f] border border-[#1e1e2e] rounded-xl p-5 text-[12px] leading-relaxed text-gray-300 font-mono overflow-x-auto">{REGISTRY}</pre>
        </div>
      </Section>

      {/* §2 — The pipeline */}
      <Section className="py-16">
        <div className="max-w-4xl mx-auto px-6">
          <h2 className="text-2xl font-bold mb-2 font-['Instrument_Sans',sans-serif]">2 · The pipeline</h2>
          <p className="text-gray-400 max-w-3xl mb-8 leading-relaxed">
            18 stages, <span className="font-mono text-white">A1 → B9</span>. Phase A gathers and widens;
            Phase B builds the graph, propagates confidence, scores, and aggregates the final identity.
            Every stage below is real — read straight from the orchestrator.
          </p>
          <div className="bg-[#12121a] border border-[#1e1e2e] rounded-xl overflow-hidden">
            {LADDER.map(([stage, purpose], i) => (
              <div key={stage} className={`flex items-baseline gap-4 px-5 py-2.5 ${i < LADDER.length - 1 ? 'border-b border-[#1e1e2e]' : ''}`}>
                <span className={`font-mono text-sm font-bold w-12 shrink-0 ${stage.startsWith('A') ? 'text-[#3388ff]' : 'text-[#00ff88]'}`}>{stage}</span>
                <span className="text-sm text-gray-300">{purpose}</span>
              </div>
            ))}
          </div>
        </div>
      </Section>

      {/* §3 — Infra rotation */}
      <Section className="py-16 bg-[#0d0d14]">
        <div className="max-w-5xl mx-auto px-6">
          <h2 className="text-2xl font-bold mb-2 font-['Instrument_Sans',sans-serif]">3 · Infra rotation</h2>
          <p className="text-gray-400 max-w-3xl mb-6 leading-relaxed">
            Two rotation mechanisms keep the producer fleet alive without manual intervention:
          </p>
          <ul className="text-gray-400 max-w-3xl mb-8 space-y-3 leading-relaxed">
            <li><span className="text-white font-semibold">Key substitution.</span> URL templates substitute
              env-var keys at dispatch time. The <span className="font-mono text-[#aa66ff]">S217 placeholder-guard</span>
              {' '}skips dispatch if a template still contains a literal <span className="font-mono">placeholder</span>
              {' '}after substitution (missing key) — no unauthenticated requests go out. Premium scanners
              (virustotal / shodan / intelx / hunter / dehashed) gate on keys → silently empty on the free tier.</li>
            <li><span className="text-white font-semibold">Search-backend rotation.</span> The
              {' '}<span className="font-mono">ddgs</span> client rotates vqd tokens and backends to survive
              rate-walls; on absence or error it falls back to raw-HTML scraping.</li>
          </ul>
          <div className="rounded-xl border border-[#aa66ff]/30 bg-[#aa66ff]/[0.04] px-5 py-3 mb-8 text-sm text-gray-400 max-w-3xl">
            <span className="text-[#aa66ff] font-semibold">No proxy layer.</span> The engine never cycles outbound
            IPs through a proxy pool — no such mechanism exists in the code.
            <span className="font-mono"> PROXYCURL_API_KEY</span> is a provider key for LinkedIn enrichment —
            a connector, not infrastructure that cycles anything.
          </div>

          <h3 className="text-sm font-mono text-gray-500 uppercase tracking-wider mb-3">Env-var key inventory — values never shown</h3>
          <div className="bg-[#12121a] border border-[#1e1e2e] rounded-xl overflow-hidden overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-[#1e1e2e] bg-[#0a0a0f]">
                  <th className="text-left py-3 px-4 text-xs font-semibold uppercase tracking-wider text-gray-500">Key name</th>
                  <th className="text-left py-3 px-4 text-xs font-semibold uppercase tracking-wider text-gray-500">Provider</th>
                  <th className="text-left py-3 px-4 text-xs font-semibold uppercase tracking-wider text-[#00ff88]">Bound module</th>
                </tr>
              </thead>
              <tbody>
                {KEYS.map(([k, prov, mod]) => (
                  <tr key={k} className="border-b border-[#1e1e2e] last:border-0 hover:bg-[#0a0a0f]/50">
                    <td className="py-2.5 px-4 font-mono text-[12px] text-gray-300">{k}</td>
                    <td className="py-2.5 px-4 text-gray-400">{prov}</td>
                    <td className="py-2.5 px-4 font-mono text-[12px] text-gray-500">{mod}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </Section>

      {/* §4 — Scoring chain */}
      <Section className="py-16">
        <div className="max-w-4xl mx-auto px-6">
          <h2 className="text-2xl font-bold mb-2 font-['Instrument_Sans',sans-serif]">4 · Scoring chain</h2>
          <p className="text-gray-400 max-w-3xl mb-8 leading-relaxed">
            Findings don&apos;t become an identity by piling up. The chain weights by source, rewards
            independent corroboration, propagates across the graph, and caps low-entropy collisions.
            <span className="text-white"> Volume is not confidence — corroboration is.</span>
          </p>
          <div className="space-y-4 mb-10">
            {[
              ['Source reliability', 'Each module carries a SOURCE_RELIABILITY weight. Finding confidence = reliability × verification × cross-reference count.'],
              ['A1 cross-verify', 'Independent sources agreeing boost each other — corroboration-as-confidence, not volume.'],
              ['B2 PageRank propagation', 'confidence_propagator.py spreads confidence across the identity graph — DAMPING 0.85, 20 iterations, MIN_DELTA 0.001.'],
              ['Collision guard (S261)', 'Quarantines low-entropy-name collisions + applies coherence caps. Operator-asserted is the only path to 100% confidence.'],
              ['B4 score engine', '0–100 exposure + threat, category-weighted (EXPOSURE_CATEGORIES + THREAT_CATEGORIES).'],
            ].map(([t, b]) => (
              <div key={t} className="flex gap-4">
                <div className="w-1 shrink-0 rounded-full bg-[#00ff88]/40" />
                <div>
                  <div className="text-sm font-semibold text-white">{t}</div>
                  <div className="text-sm text-gray-400 leading-relaxed">{b}</div>
                </div>
              </div>
            ))}
          </div>

          <h3 className="text-sm font-mono text-gray-500 uppercase tracking-wider mb-3">Severity → confidence map</h3>
          <div className="flex flex-wrap gap-3 mb-10">
            {SEVERITY.map(([sev, conf]) => (
              <div key={sev} className="bg-[#12121a] border border-[#1e1e2e] rounded-lg px-4 py-2 text-center">
                <div className="text-[11px] font-mono text-gray-500 uppercase">{sev}</div>
                <div className="text-lg font-mono font-bold text-[#00ff88]">{conf}</div>
              </div>
            ))}
          </div>
          <p className="text-sm text-gray-500 max-w-3xl mb-8">
            Intelligence inferences rank below platform-confirmed data — an inferred signal never outweighs
            a directly observed one.
          </p>

          <div className="border-t border-[#1e1e2e] pt-8">
            <p className="text-gray-400">
              These scored axes feed the{' '}
              <Link to="/doc/bfp" className="text-[#00ff88] hover:underline">BFP layer</Link>
              {' '}— the entropy + fingerprint substrate that turns a scored identity into a portable,
              auditable behavioral hash.
            </p>
          </div>
        </div>
      </Section>
    </div>
  )
}
