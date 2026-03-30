import Section from '../shared/Section'
import GenerativeAvatar from '../GenerativeAvatar'
import { CollectDiagram, GraphDiagram, PropagateDiagram, ScoreDiagram, GeoMapDiagram } from './Diagrams'

export function StageCollect() {
  return (
    <Section className="py-20">
      <div className="max-w-4xl mx-auto px-6">
        <div className="grid md:grid-cols-2 gap-12 items-center">
          <div>
            <div className="inline-block text-[10px] font-mono text-[#00ff88] bg-[#00ff88]/10 px-2 py-0.5 rounded-full mb-2">DISCOVER — EMAIL-BASED</div>
            <div className="text-6xl font-mono font-bold text-[#00ff88]/15 mb-2">01</div>
            <h2 className="text-2xl font-bold mb-3 font-['Instrument_Sans',sans-serif]">Discover</h2>
            <p className="text-gray-400 mb-4">
              Every identity investigation starts with a single anchor: an email address.
              xposeTIP scans <span className="text-white font-semibold">120 sources</span> in parallel —
              social networks, breach databases, archives, gaming platforms, developer registries, professional networks.
            </p>
            <p className="text-sm text-gray-500">
              Each source carries a reliability weight. A GitHub profile (<span className="text-[#00ff88] font-mono">0.85</span>)
              contributes more to the identity graph than an anonymous scraper (<span className="text-gray-400 font-mono">0.60</span>).
              The goal isn't to collect more data — it's to collect <span className="text-white">the right data</span> about a person.
            </p>
            <p className="text-sm text-gray-500 mt-3">
              After the initial email scan, <span className="text-white">Pass 1.5</span> takes every
              discovered username and expands the search — finding accounts the email alone
              would miss. Then <span className="text-white">Pass 2</span> uses the resolved
              name to search news, sanctions, and corporate registries.
            </p>
          </div>
          <CollectDiagram />
        </div>
      </div>
    </Section>
  )
}

export function StageGraph() {
  return (
    <Section className="py-20 bg-[#12121a]/50">
      <div className="max-w-4xl mx-auto px-6">
        <div className="grid md:grid-cols-2 gap-12 items-center">
          <GraphDiagram />
          <div>
            <div className="text-6xl font-mono font-bold text-[#3388ff]/15 mb-2">02</div>
            <h2 className="text-2xl font-bold mb-3 font-['Instrument_Sans',sans-serif]">Connect</h2>
            <p className="text-gray-400 mb-4">
              Raw data becomes an <span className="text-white font-semibold">identity graph</span>.
              Every account, username, breach, and name becomes a node.
              Every relationship becomes a weighted edge.
            </p>
            <div className="space-y-2 text-sm font-mono text-gray-500">
              <div><span className="text-[#00ff88]">email</span> → <span className="text-[#ff8800]">username</span> → <span className="text-[#3388ff]">platform</span></div>
              <div><span className="text-[#00ff88]">email</span> → <span className="text-[#ff2244]">breach</span> → <span className="text-gray-400">data_classes</span></div>
              <div><span className="text-[#ff8800]">username</span> → <span className="text-[#00ddcc]">name</span> <span className="text-gray-600">(identified_as)</span></div>
            </div>
            <p className="text-sm text-gray-500 mt-4">
              This graph is the foundation. Traditional TI sees isolated indicators.
              xposeTIP sees <span className="text-white">how they're connected</span> — which is what makes a person identifiable.
            </p>
          </div>
        </div>
      </div>
    </Section>
  )
}

export function StagePropagate() {
  return (
    <Section className="py-20">
      <div className="max-w-4xl mx-auto px-6">
        <div className="grid md:grid-cols-2 gap-12 items-center">
          <div>
            <div className="text-6xl font-mono font-bold text-[#ffcc00]/15 mb-2">03</div>
            <h2 className="text-2xl font-bold mb-3 font-['Instrument_Sans',sans-serif]">Propagate</h2>
            <p className="text-gray-400 mb-4">
              <span className="text-white font-semibold">Personalized PageRank</span> walks the identity graph.
              Confidence flows outward from the email anchor through edges weighted by source reliability.
            </p>
            <p className="text-sm text-gray-500 mb-3">
              A name confirmed by 3 independent sources through different graph paths accumulates
              more confidence than a name from a single scraper. The algorithm separates signal from noise
              automatically — no manual triage needed.
            </p>
            <p className="text-sm text-gray-500">
              The teleport probability always returns to the seed email — this is <span className="text-[#ffcc00]">Personalized PageRank</span>,
              not standard PageRank. The anchor never loses its authority. Every confidence score is traceable.
            </p>
          </div>
          <PropagateDiagram />
        </div>
      </div>
    </Section>
  )
}

export function StageScore() {
  return (
    <Section className="py-20 bg-[#12121a]/50">
      <div className="max-w-4xl mx-auto px-6">
        <div className="grid md:grid-cols-2 gap-12 items-center">
          <ScoreDiagram />
          <div>
            <div className="text-6xl font-mono font-bold text-[#ff8800]/15 mb-2">04</div>
            <h2 className="text-2xl font-bold mb-3 font-['Instrument_Sans',sans-serif]">Score</h2>
            <p className="text-gray-400 mb-4">
              Two scores capture two different risks. Because being visible isn't the same as being in danger.
            </p>
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
            <p className="text-xs text-gray-500 font-mono">
              weight = severity × source_reliability × graph_confidence
            </p>
          </div>
        </div>
      </div>
    </Section>
  )
}

export function StageIdentify({ demoSeed }) {
  return (
    <Section className="py-20">
      <div className="max-w-4xl mx-auto px-6">
        <div className="grid md:grid-cols-2 gap-12 items-center">
          <div>
            <div className="text-6xl font-mono font-bold text-[#ff2244]/15 mb-2">05</div>
            <h2 className="text-2xl font-bold mb-3 font-['Instrument_Sans',sans-serif]">Identify</h2>
            <p className="text-gray-400 mb-4">
              Every identity gets a <span className="text-white font-semibold">digital DNA</span> — a 9-axis behavioral fingerprint
              that's unique, persistent, and impossible to fake. Unlike an IP address, this fingerprint
              doesn't change when the person moves to a new server.
            </p>
            <p className="text-sm text-gray-500 mb-3">
              Personas are clustered automatically. Names are resolved through family consensus —
              if 3 sources say "Theis", a single outlier won't override the majority.
              A unique pixel avatar is generated from the graph topology — ~5.4 billion combinations.
            </p>
            <p className="text-sm text-gray-500">
              Green face = low risk. Red glitched face = high threat.
              The avatar is a visual summary of the entire identity.
            </p>
          </div>
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
        </div>
      </div>
    </Section>
  )
}

export function StageExpose() {
  return (
    <Section className="py-20 bg-[#12121a]/50">
      <div className="max-w-4xl mx-auto px-6">
        <div className="grid md:grid-cols-2 gap-12 items-center">
          <div>
            <div className="inline-block text-[10px] font-mono text-[#ff2244] bg-[#ff2244]/10 px-2 py-0.5 rounded-full mb-2">ENRICH — NAME-BASED</div>
            <div className="text-6xl font-mono font-bold text-[#ff2244]/15 mb-2">06</div>
            <h2 className="text-2xl font-bold mb-3 font-['Instrument_Sans',sans-serif]">Enrich</h2>
            <p className="text-gray-400 mb-4">
              Once the identity has a high-confidence name, a second pass runs
              <span className="text-white font-semibold"> name-based intelligence</span> across three independent layers.
              This separation ensures name searches only fire with verified identities.
            </p>
            <p className="text-sm text-gray-500 mb-3">
              Three layers, zero cascade risk. Each layer fails independently.
              All matches are <span className="text-[#ffcc00]">potential</span> — never auto-confirmed. The operator decides.
            </p>
          </div>
          <div className="space-y-3">
            {[
              { layer: 'MEDIA', color: '#3388ff', items: ['GDELT (deep archive)', 'GNews (curated)', 'Google News RSS (fallback)'], desc: 'Global news monitoring' },
              { layer: 'COMPLIANCE', color: '#ff8800', items: ['OpenSanctions (40+ lists)', 'Interpol Red Notices'], desc: 'Sanctions & PEP screening' },
              { layer: 'CORPORATE', color: '#aa55ff', items: ['OpenCorporates', 'LBR Luxembourg'], desc: 'Directorship tracking' },
            ].map(l => (
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
        </div>
      </div>
    </Section>
  )
}

export function StageMeasure() {
  return (
    <Section className="py-20">
      <div className="max-w-4xl mx-auto px-6">
        <div className="text-6xl font-mono font-bold text-[#aa55ff]/15 mb-2 text-center">07</div>
        <h2 className="text-2xl font-bold mb-4 text-center font-['Instrument_Sans',sans-serif]">Fingerprint</h2>
        <p className="text-gray-400 text-center mb-4 max-w-xl mx-auto">
          The 9-axis behavioral radar is the identity's <span className="text-white font-semibold">digital DNA</span>.
          Each axis independently measures a dimension of the person's online presence.
          Unlike an IP, this fingerprint persists.
        </p>
        <p className="text-gray-500 text-center text-sm mb-8 max-w-lg mx-auto">
          Today it's a report. Tomorrow these fingerprints feed SIEMs and firewalls —
          blocking behaviors, not addresses.
        </p>
        <div className="grid md:grid-cols-3 gap-3">
          {[
            { axis: 'accounts', color: '#00ff88', desc: 'Number of online accounts', sources: 'Holehe, scraper engine, social enricher' },
            { axis: 'platforms', color: '#3388ff', desc: 'Diversity of platform types', sources: 'Social, dev, gaming, professional' },
            { axis: 'email_age', color: '#ffcc00', desc: 'How long the email has existed', sources: 'Breach dates, archive snapshots' },
            { axis: 'breaches', color: '#ff2244', desc: 'Breach exposure count', sources: 'HIBP, LeakCheck, IntelX' },
            { axis: 'username_reuse', color: '#ff8800', desc: 'Same username across sites', sources: 'Cross-platform matching' },
            { axis: 'data_leaked', color: '#cc88ff', desc: 'Volume of exposed data', sources: 'Breach content analysis' },
            { axis: 'geo_spread', color: '#00ddcc', desc: 'Geographic distribution', sources: 'GeoIP, self-reported, timezone, nationalize, language, geo consistency' },
            { axis: 'security', color: '#888888', desc: 'Security posture', sources: 'SPF, DKIM, DMARC, security headers' },
            { axis: 'public_exposure', color: '#ff5588', desc: 'Media + sanctions + corporate visibility', sources: 'GDELT, GNews, OpenSanctions, Interpol' },
          ].map(a => (
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
      </div>
    </Section>
  )
}

export function StageLocate() {
  return (
    <Section className="py-20 bg-[#12121a]/50">
      <div className="max-w-4xl mx-auto px-6">
        <div className="grid md:grid-cols-2 gap-12 items-center">
          <GeoMapDiagram />
          <div>
            <div className="text-6xl font-mono font-bold text-[#00ddcc]/15 mb-2">08</div>
            <h2 className="text-2xl font-bold mb-3 font-['Instrument_Sans',sans-serif]">Locate</h2>
            <p className="text-gray-400 mb-4">
              Self-reported locations from profiles are <span className="text-white font-semibold">geocoded</span> and
              separated from mail server IP locations. The difference matters:
              GeoIP tells you where Google's servers are. xposeTIP tells you where the <span className="text-[#00ddcc]">person</span> is.
            </p>
            <p className="text-sm text-gray-500 mb-3">
              30+ countries, 20+ cities — zero external API calls. All geocoding runs locally.
            </p>
            <p className="text-sm text-gray-500">
              The geographic dimension adds context that IP-based intelligence misses entirely.
              A person's location is part of their identity — not an indicator that expires.
            </p>
          </div>
        </div>
      </div>
    </Section>
  )
}
