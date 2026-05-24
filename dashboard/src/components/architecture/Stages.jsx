// S206-3 — Stages.jsx 408 LOC → ~200 LOC array-driven.
// 11 quasi-identical stage components migrated into STAGES_DATA + generic
// <StageBlock />. Special cases (Identify avatar, Enrich layer cards,
// Fingerprint full-width axes grid) handled via diagram-type discriminator.
// Per S206-3 rule: paragraph TEXT content preserved verbatim; only the
// outer JSX structure changed. Per-stage color preserved (not re-painted).

import Section from '../shared/Section'
import GenerativeAvatar from '../GenerativeAvatar'
import { CollectDiagram, GraphDiagram, PropagateDiagram, ScoreDiagram, GeoMapDiagram, CascadeDiagram, SimilarityDiagram, DiscoveryDiagram } from './Diagrams'

const STAGES_DATA = [
  {
    num: '01',
    color: '#00ff88',
    label: 'DISCOVER — EMAIL-BASED',
    title: 'Discover',
    side: 'right',
    bg: false,
    paragraphs: [
      { tone: 'lead',   html: `Every identity investigation starts with a single anchor: an email address. xposeTIP scans <span class="text-white font-semibold">170 sources</span> in parallel — social networks, breach databases, archives, gaming platforms, developer registries, professional networks.` },
      { tone: 'detail', html: `Each source carries a reliability weight. A GitHub profile (<span class="text-[#00ff88] font-mono">0.85</span>) contributes more to the identity graph than an anonymous scraper (<span class="text-gray-400 font-mono">0.60</span>). The goal isn't to collect more data — it's to collect <span class="text-white">the right data</span> about a person.` },
      { tone: 'detail', html: `After the initial email scan, the pipeline branches: <span class="text-white">Pass 1.5</span> takes every discovered username and expands the search, <span class="text-white">A1.5/A1.6</span> extract phone numbers and crypto wallets from breach payloads, <span class="text-white">A3.5</span> dispatches name-based scrapers once a primary name is resolved, and <span class="text-white">Pass 2</span> uses the resolved name to search news, sanctions, corporate registries, and legal records.` },
    ],
    diagram: { kind: 'component', Comp: CollectDiagram },
  },
  {
    num: '02',
    color: '#3388ff',
    label: null,
    title: 'Connect',
    side: 'left',
    bg: true,
    paragraphs: [
      { tone: 'lead', html: `Raw data becomes an <span class="text-white font-semibold">identity graph</span>. Every account, username, breach, and name becomes a node. Every relationship becomes a weighted edge.` },
      { tone: 'edges-block' },
      { tone: 'detail', html: `This graph is the foundation. Traditional TI sees isolated indicators. xposeTIP sees <span class="text-white">how they're connected</span> — which is what makes a person identifiable. Cross-referenced findings (same indicator surfaced by ≥ 2 independent scrapers) earn a <span class="text-[#3388ff] font-mono"> +0.15</span> confidence boost — independence compounds.` },
    ],
    diagram: { kind: 'component', Comp: GraphDiagram },
  },
  {
    num: '03',
    color: '#ffcc00',
    label: null,
    title: 'Propagate',
    side: 'right',
    bg: false,
    paragraphs: [
      { tone: 'lead',   html: `<span class="text-white font-semibold">Personalized PageRank</span> walks the identity graph. Confidence flows outward from the email anchor through edges weighted by source reliability.` },
      { tone: 'detail', html: `A name confirmed by 3 independent sources through different graph paths accumulates more confidence than a name from a single scraper. The algorithm separates signal from noise automatically — no manual triage needed.` },
      { tone: 'detail', html: `The teleport probability always returns to the seed email — this is <span class="text-[#ffcc00]">Personalized PageRank</span>, not standard PageRank (<span class="font-mono">damping=0.85 · 20 iterations</span>). The anchor never loses its authority. Every confidence score is traceable.` },
    ],
    diagram: { kind: 'component', Comp: PropagateDiagram },
  },
  {
    num: '04',
    color: '#ff8800',
    label: null,
    title: 'Score',
    side: 'left',
    bg: true,
    paragraphs: [
      { tone: 'lead',   html: `Two scores capture two different risks. Because being visible isn't the same as being in danger.` },
      { tone: 'score-block' },
      { tone: 'detail-mono', html: `weight = severity × source_reliability × graph_confidence` },
    ],
    diagram: { kind: 'component', Comp: ScoreDiagram },
  },
  {
    num: '05',
    color: '#ff2244',
    label: null,
    title: 'Identify',
    side: 'right',
    bg: false,
    paragraphs: [
      { tone: 'lead',   html: `Every identity gets a <span class="text-white font-semibold">digital DNA</span> — an 11-axis behavioral fingerprint that's unique, persistent, and impossible to fake. Unlike an IP address, this fingerprint doesn't change when the person moves to a new server.` },
      { tone: 'detail', html: `Personas are clustered automatically. Names are resolved through family consensus — if 3 sources say "Theis", a single outlier won't override the majority. A unique pixel avatar is generated from the graph topology — ~5.4 billion combinations.` },
      { tone: 'detail', html: `Green face = low risk. Red glitched face = high threat. The avatar is a visual summary of the entire identity.` },
      { tone: 'detail', html: `When a real photo is found, the glyph becomes a <span class="text-white">32 × 32 badge</span> overlaying the photo — Snapchat-Bitmoji style. The full <span class="text-white">Fingerprint Evolution</span> timeline scrolls through every snapshot (up to 20) — every scan is a frame, every frame is auditable.` },
    ],
    diagram: { kind: 'identify-avatars' },
  },
  {
    num: '06',
    color: '#ff2244',
    label: 'ENRICH — NAME-BASED',
    title: 'Enrich',
    side: 'right',
    bg: true,
    paragraphs: [
      { tone: 'lead',   html: `Once the identity has a high-confidence name, a second pass runs <span class="text-white font-semibold"> name-based intelligence</span> across three independent layers. This separation ensures name searches only fire with verified identities.` },
      { tone: 'detail', html: `Four layers, zero cascade risk. Each layer fails independently. All matches are <span class="text-[#ffcc00]">potential</span> — never auto-confirmed. The operator decides.` },
    ],
    diagram: { kind: 'enrich-layers' },
  },
  {
    num: '07',
    color: '#aa55ff',
    label: null,
    title: 'Fingerprint',
    layout: 'full',  // full-width, centered title + axes grid
    bg: false,
    paragraphs: [
      { tone: 'centered', html: `The 11-axis behavioral radar is the identity's <span class="text-white font-semibold">digital DNA</span>. Each axis independently measures a dimension of the person's online presence. Unlike an IP, this fingerprint persists.` },
      { tone: 'centered-subtle', html: `Today it's a report. Tomorrow these fingerprints feed SIEMs and firewalls — blocking behaviors, not addresses. Phone numbers, crypto wallets, and legal records all feed existing axes — new data, no new axes, no scope creep.` },
    ],
    diagram: { kind: 'fingerprint-axes' },
  },
  {
    num: '08',
    color: '#00ddcc',
    label: null,
    title: 'Locate',
    side: 'left',
    bg: true,
    paragraphs: [
      { tone: 'lead',   html: `Self-reported locations from profiles are <span class="text-white font-semibold">geocoded</span> and separated from mail server IP locations. The difference matters: GeoIP tells you where Google's servers are. xposeTIP tells you where the <span class="text-[#00ddcc]">person</span> is.` },
      { tone: 'detail', html: `Rendered with <span class="text-white">TopoJSON 110m</span> via D3 Natural Earth projection — a country-density heatmap, zoom 1–8×, ground-truth locations marked in gold. 132+ countries indexed. Zero external map tile calls.` },
      { tone: 'detail', html: `The geographic dimension adds context that IP-based intelligence misses entirely. A person's location is part of their identity — not an indicator that expires.` },
    ],
    diagram: { kind: 'component', Comp: GeoMapDiagram },
  },
  {
    num: '09',
    color: '#88aaff',
    label: 'OBSERVE — STATE MACHINE',
    title: 'Cascade',
    side: 'right',
    bg: false,
    paragraphs: [
      { tone: 'lead',   html: `When a scan ends, intelligence doesn't appear all at once. The cascade state machine breaks the post-scan lifecycle into <span class="text-white font-semibold">four visible states</span>, tracked in real time by the UI.` },
      { tone: 'detail', html: `From <span class="text-[#88aaff] font-mono">gathering</span> (Phase A finishing) → <span class="text-[#ff8800] font-mono"> computing</span> (Phase B running graph, score, profile, persona, fingerprint) → <span class="text-[#aa55ff] font-mono"> similarity</span> (recompute fired) → <span class="text-[#00ff88] font-mono"> done</span>.` },
      { tone: 'detail', html: `Audit-grade transitions logged in <span class="text-white font-mono">scans.cascade_state</span> (Alembic 014). The user always knows what's happening — no black-box waits, no silent failures.` },
    ],
    diagram: { kind: 'component', Comp: CascadeDiagram },
  },
  {
    num: '10',
    color: '#cc88ff',
    label: 'RELATE — PERSISTED',
    title: 'Similarity',
    side: 'left',
    bg: true,
    paragraphs: [
      { tone: 'lead',   html: `Every scan triggers an <span class="text-white font-semibold">11-axis cosine similarity recompute</span> against every other identity in the workspace.` },
      { tone: 'detail', html: `Results land in <span class="text-white font-mono">target_similarities</span> (Alembic 013) with a <span class="text-[#cc88ff] font-mono"> first_detected</span> timestamp preserved across recomputes — audit-grade history.` },
      { tone: 'detail', html: `Threshold <span class="text-[#cc88ff] font-mono">0.70</span>. Top matches surface on the Overview block. Same person across two emails? The platform sees it. Different person, same behavioral signature? The platform sees that too.` },
      { tone: 'detail', html: `This is the foundation for the <span class="text-white">Behavioral Fingerprint Protocol</span> — what comes after IOC sharing.` },
    ],
    diagram: { kind: 'component', Comp: SimilarityDiagram },
  },
  {
    num: '11',
    color: '#ffaa55',
    label: 'EXPAND — OPERATOR-TRIGGERED',
    title: 'Web Discovery',
    side: 'right',
    bg: false,
    paragraphs: [
      { tone: 'lead',     html: `The 170 scrapers are predictable. The open web isn't. Phase C — <span class="text-white font-semibold">adaptive web crawling</span> — fires when the operator triggers it.` },
      { tone: 'detail',   html: `The identity's fingerprint generates Google dork queries, fetches pages via trafilatura, and runs <span class="text-white">6 extractors</span> (<span class="font-mono text-[#ffaa55]">rel-me · JSON-LD · social link · email · meta tag · username</span>).` },
      { tone: 'detail',   html: `A quality gate dedupes against existing findings. Survivors land in <span class="text-white font-mono">discovery_leads</span> for operator review — separate workflow, never auto-promoted to the identity graph.` },
      { tone: 'footnote', html: `Budget: 20 queries · 50 pages · 60 seconds — green intelligence applies to crawls too.` },
    ],
    diagram: { kind: 'component', Comp: DiscoveryDiagram },
  },
]

// ── Special diagram renderers (Identify avatars, Enrich layer cards, Fingerprint axes grid) ──
function IdentifyAvatarsBlock({ demoSeed }) {
  return (
    <div className="flex flex-col items-center gap-6">
      <div className="bg-[#12121a] border border-[#1e1e2e] rounded-xl p-6 flex flex-col items-center gap-3">
        <GenerativeAvatar seed={demoSeed} size={64} score={42} />
        <span className="text-[10px] text-gray-600 font-mono">identity glyph · score 42</span>
      </div>
      <div className="grid grid-cols-4 gap-3">
        {[12, 37, 58, 85].map(score => (
          <div key={score} className="flex flex-col items-center gap-1">
            <GenerativeAvatar
              seed={{ ...demoSeed, email_hash: demoSeed.email_hash + score * 100 }}
              size={32}
              score={score}
            />
            <span className="text-[9px] text-gray-600 font-mono">{score}</span>
          </div>
        ))}
      </div>
    </div>
  )
}

const ENRICH_LAYERS = [
  { layer: 'MEDIA',      color: '#3388ff', items: ['GDELT (deep archive)', 'GNews (curated)', 'Google News RSS (fallback)'], desc: 'Global news monitoring' },
  { layer: 'COMPLIANCE', color: '#ff8800', items: ['OpenSanctions (40+ lists)', 'Interpol Red Notices'],                       desc: 'Sanctions & PEP screening' },
  { layer: 'CORPORATE',  color: '#aa55ff', items: ['OpenCorporates', 'LBR Luxembourg'],                                         desc: 'Directorship tracking' },
  { layer: 'LEGAL',      color: '#cc88ff', items: ['Courtlistener (US federal)', 'BODACC (FR)', 'UK Gazette (London/Edinburgh/Belfast)'], desc: 'Person-centric legal records' },
]

function EnrichLayersBlock() {
  return (
    <div className="space-y-3">
      {ENRICH_LAYERS.map(l => (
        <div key={l.layer} className="bg-[#0a0a0f] border border-[#1e1e2e] rounded-lg p-4">
          <div className="flex items-center gap-2 mb-2">
            <span className="text-xs font-mono font-bold" style={{ color: l.color }}>{l.layer}</span>
            <span className="text-[10px] text-gray-600">{l.desc}</span>
          </div>
          <div className="flex flex-wrap gap-1.5">
            {l.items.map(i => (
              <span key={i} className="text-[10px] font-mono text-gray-400 bg-[#1e1e2e] px-2 py-0.5 rounded">{i}</span>
            ))}
          </div>
        </div>
      ))}
      <p className="text-[10px] text-gray-600 font-mono mt-2">
        Confidence threshold: &ge; 0.60 &middot; match_type = "potential"
      </p>
    </div>
  )
}

const FINGERPRINT_AXES = [
  { axis: 'accounts',         color: '#00ff88', desc: 'Number of online accounts',          sources: 'Holehe, scraper engine, social enricher' },
  { axis: 'platforms',        color: '#3388ff', desc: 'Diversity of platform types',        sources: 'Social, dev, gaming, professional' },
  { axis: 'email_age',        color: '#ffcc00', desc: 'How long the email has existed',     sources: 'Breach dates, archive snapshots' },
  { axis: 'breaches',         color: '#ff2244', desc: 'Breach exposure count',              sources: 'HIBP, LeakCheck, IntelX' },
  { axis: 'username_reuse',   color: '#ff8800', desc: 'Same username across sites',         sources: 'Cross-platform matching' },
  { axis: 'data_leaked',      color: '#cc88ff', desc: 'Volume of exposed data',             sources: 'Breach content analysis' },
  { axis: 'geo_spread',       color: '#00ddcc', desc: 'Geographic distribution',            sources: 'GeoIP, self-reported, timezone, nationalize, language, geo consistency' },
  { axis: 'security',         color: '#888888', desc: 'Security posture',                   sources: 'SPF, DKIM, DMARC, security headers' },
  { axis: 'public_exposure',  color: '#ff5588', desc: 'Media + sanctions + corporate visibility', sources: 'GDELT, GNews, OpenSanctions, Interpol' },
]

function FingerprintAxesBlock() {
  return (
    <div className="grid md:grid-cols-3 gap-3">
      {FINGERPRINT_AXES.map(a => (
        <div key={a.axis} className="bg-[#0a0a0f] border border-[#1e1e2e] rounded-lg p-3">
          <div className="flex items-center gap-2 mb-1">
            <span className="w-2 h-2 rounded-full" style={{ backgroundColor: a.color }} />
            <span className="text-xs font-mono font-semibold" style={{ color: a.color }}>{a.axis}</span>
          </div>
          <p className="text-xs text-gray-400 mb-1">{a.desc}</p>
          <p className="text-[10px] text-gray-600">{a.sources}</p>
        </div>
      ))}
    </div>
  )
}

// ── Per-stage block ──
function Paragraph({ p, stage }) {
  if (p.tone === 'edges-block') {
    return (
      <div className="space-y-2 text-sm font-mono text-gray-500">
        <div><span className="text-[#00ff88]">email</span> → <span className="text-[#ff8800]">username</span> → <span className="text-[#3388ff]">platform</span></div>
        <div><span className="text-[#00ff88]">email</span> → <span className="text-[#ff2244]">breach</span> → <span className="text-gray-400">data_classes</span></div>
        <div><span className="text-[#ff8800]">username</span> → <span className="text-[#00ddcc]">name</span> <span className="text-gray-600">(identified_as)</span></div>
      </div>
    )
  }
  if (p.tone === 'score-block') {
    return (
      <div className="space-y-3 mb-4">
        <div className="bg-[#0a0a0f] rounded-lg p-3">
          <div className="text-sm font-semibold text-[#00ff88]">EXPOSURE</div>
          <div className="text-xs text-gray-500">How much of this identity is publicly visible</div>
        </div>
        <div className="bg-[#0a0a0f] rounded-lg p-3">
          <div className="text-sm font-semibold text-[#ff2244]">THREAT</div>
          <div className="text-xs text-gray-500">How dangerous that exposure is — breaches, leaked credentials, sanctions</div>
        </div>
      </div>
    )
  }
  if (p.tone === 'lead') {
    return <p className="text-gray-400 mb-4" dangerouslySetInnerHTML={{ __html: p.html }} />
  }
  if (p.tone === 'detail') {
    return <p className="text-sm text-gray-500 mb-3" dangerouslySetInnerHTML={{ __html: p.html }} />
  }
  if (p.tone === 'detail-mono') {
    return <p className="text-xs text-gray-500 font-mono" dangerouslySetInnerHTML={{ __html: p.html }} />
  }
  if (p.tone === 'footnote') {
    return <p className="text-[10px] text-gray-600 font-mono mt-4" dangerouslySetInnerHTML={{ __html: p.html }} />
  }
  if (p.tone === 'centered') {
    return <p className="text-gray-400 text-center mb-4 max-w-xl mx-auto" dangerouslySetInnerHTML={{ __html: p.html }} />
  }
  if (p.tone === 'centered-subtle') {
    return <p className="text-gray-500 text-center text-sm mb-8 max-w-lg mx-auto" dangerouslySetInnerHTML={{ __html: p.html }} />
  }
  return null
}

function StageBlock({ stage, demoSeed }) {
  const sectionBg = stage.bg ? 'bg-[#12121a]/50' : ''

  // ── FULL-WIDTH layout (Fingerprint, Stage 07) ──
  if (stage.layout === 'full') {
    return (
      <Section className={`py-20 ${sectionBg}`}>
        <div className="max-w-4xl mx-auto px-6">
          <div className="text-6xl font-mono font-bold mb-2 text-center" style={{ color: `${stage.color}26` }}>
            {stage.num}
          </div>
          <h2 className="text-2xl font-bold mb-4 text-center font-['Instrument_Sans',sans-serif]">{stage.title}</h2>
          {stage.paragraphs.map((p, i) => <Paragraph key={i} p={p} stage={stage} />)}
          {stage.diagram?.kind === 'fingerprint-axes' && <FingerprintAxesBlock />}
        </div>
      </Section>
    )
  }

  // ── SPLIT layout (text + diagram) ──
  const TextBlock = (
    <div>
      {stage.label && (
        <div className="inline-block text-[10px] font-mono px-2 py-0.5 rounded-full mb-2"
             style={{ color: stage.color, backgroundColor: `${stage.color}1a` }}>
          {stage.label}
        </div>
      )}
      <div className="text-6xl font-mono font-bold mb-2" style={{ color: `${stage.color}26` }}>
        {stage.num}
      </div>
      <h2 className="text-2xl font-bold mb-3 font-['Instrument_Sans',sans-serif]">{stage.title}</h2>
      {stage.paragraphs.map((p, i) => <Paragraph key={i} p={p} stage={stage} />)}
    </div>
  )

  const DiagramBlock = (() => {
    if (stage.diagram?.kind === 'component') {
      const Comp = stage.diagram.Comp
      return <Comp />
    }
    if (stage.diagram?.kind === 'identify-avatars') {
      return <IdentifyAvatarsBlock demoSeed={demoSeed} />
    }
    if (stage.diagram?.kind === 'enrich-layers') {
      return <EnrichLayersBlock />
    }
    return null
  })()

  return (
    <Section className={`py-20 ${sectionBg}`}>
      <div className="max-w-4xl mx-auto px-6">
        <div className="grid md:grid-cols-2 gap-12 items-center">
          {stage.side === 'right' ? (
            <>
              {TextBlock}
              {DiagramBlock}
            </>
          ) : (
            <>
              {DiagramBlock}
              {TextBlock}
            </>
          )}
        </div>
      </div>
    </Section>
  )
}

export default function Stages({ demoSeed }) {
  return (
    <>
      {STAGES_DATA.map((stage, i) => (
        <StageBlock key={i} stage={stage} demoSeed={demoSeed} />
      ))}
    </>
  )
}
