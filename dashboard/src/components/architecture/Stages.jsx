import Section from '../shared/Section'
import GenerativeAvatar from '../GenerativeAvatar'
import { CollectDiagram, GraphDiagram, PropagateDiagram, ScoreDiagram, GeoMapDiagram } from './Diagrams'

export function StageCollect() {
  return (
    <Section className="py-20">
      <div className="max-w-4xl mx-auto px-6">
        <div className="grid md:grid-cols-2 gap-12 items-center">
          <div>
            <div className="inline-block text-[10px] font-mono text-[#00ff88] bg-[#00ff88]/10 px-2 py-0.5 rounded-full mb-2">PASS 1 — EMAIL-BASED</div>
            <div className="text-6xl font-mono font-bold text-[#00ff88]/15 mb-2">01</div>
            <h2 className="text-2xl font-bold mb-3 font-['Instrument_Sans',sans-serif]">Collect</h2>
            <p className="text-gray-400 mb-4">
              Your email is scanned across <span className="text-white font-semibold">110 sources</span> in parallel.
              Social networks, breach databases, archives, gaming platforms, developer registries, LinkedIn intelligence.
            </p>
            <p className="text-sm text-gray-500">
              Each source is weighted by reliability. A GitHub profile (<span className="text-[#00ff88] font-mono">0.85</span>)
              carries more weight than an anonymous scraper (<span className="text-gray-400 font-mono">0.60</span>).
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
            <h2 className="text-2xl font-bold mb-3 font-['Instrument_Sans',sans-serif]">Graph</h2>
            <p className="text-gray-400 mb-4">
              Every data point becomes a <span className="text-white font-semibold">node</span>.
              Every relationship becomes an <span className="text-white font-semibold">edge</span>.
            </p>
            <div className="space-y-2 text-sm font-mono text-gray-500">
              <div><span className="text-[#00ff88]">email</span> → <span className="text-[#ff8800]">username</span> → <span className="text-[#3388ff]">platform</span></div>
              <div><span className="text-[#00ff88]">email</span> → <span className="text-[#ff2244]">breach</span> → <span className="text-gray-400">data_classes</span></div>
              <div><span className="text-[#ff8800]">username</span> → <span className="text-[#00ddcc]">name</span> <span className="text-gray-600">(identified_as)</span></div>
            </div>
            <p className="text-sm text-gray-500 mt-4">
              This is your identity graph — a map of how your digital identity is connected across the internet.
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
              <span className="text-white font-semibold">Personalized PageRank</span> walks the graph.
              The email anchor always stays the highest-confidence node —
              confidence propagates outward through edges weighted by source reliability.
            </p>
            <p className="text-sm text-gray-500 mb-3">
              A name confirmed by 3 independent sources through different paths accumulates
              more confidence than a name from a single source.
            </p>
            <p className="text-sm text-gray-500">
              Teleport probability always returns to the seed email — this is <span className="text-[#ffcc00]">Personalized PageRank</span>,
              not standard PageRank. The anchor never loses its authority.
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
              Two scores, one identity.
            </p>
            <div className="space-y-3 mb-4">
              <div className="bg-[#0a0a0f] rounded-lg p-3">
                <div className="text-sm font-semibold text-[#00ff88]">EXPOSURE</div>
                <div className="text-xs text-gray-500">How much of you is publicly visible</div>
              </div>
              <div className="bg-[#0a0a0f] rounded-lg p-3">
                <div className="text-sm font-semibold text-[#ff2244]">THREAT</div>
                <div className="text-xs text-gray-500">How dangerous that exposure is</div>
              </div>
            </div>
            <p className="text-xs text-gray-500 font-mono">
              finding weight = severity × source_reliability × graph_confidence
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
              Every identity gets a unique <span className="text-white font-semibold">pixel avatar</span>,
              a 9-axis <span className="text-white font-semibold">digital fingerprint</span>,
              clustered <span className="text-white font-semibold">personas</span> with aliases,
              <span className="text-white font-semibold">profile photos</span> collected across platforms,
              a <span className="text-white font-semibold">geographic exposure map</span>,
              and a <span className="text-white font-semibold">life timeline</span>.
            </p>
            <p className="text-sm text-gray-500 mb-3">
              Persona names are resolved through family name consensus — if 3 sources say "Theis",
              a single outlier won't override the majority. Email-verified sources take priority
              over username-guessed matches.
            </p>
            <p className="text-sm text-gray-500">
              The avatar is generated from your graph topology — ~5.4 billion unique combinations.
              Green face = low risk. Red glitched face = high threat.
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
            <div className="inline-block text-[10px] font-mono text-[#ff2244] bg-[#ff2244]/10 px-2 py-0.5 rounded-full mb-2">PASS 2 — NAME-BASED</div>
            <div className="text-6xl font-mono font-bold text-[#ff2244]/15 mb-2">06</div>
            <h2 className="text-2xl font-bold mb-3 font-['Instrument_Sans',sans-serif]">Expose</h2>
            <p className="text-gray-400 mb-4">
              Once Pass 1 resolves a name, Pass 2 runs <span className="text-white font-semibold">name-based intelligence</span>.
              This separation ensures name-based searches only run with high-confidence names.
            </p>
            <p className="text-sm text-gray-500 mb-3">
              Three independent layers — errors don't cascade. Max 15 media + 8 corporate findings.
              All matches are <span className="text-[#ffcc00]">potential</span> — never auto-confirmed.
            </p>
          </div>
          <div className="space-y-3">
            {[
              { layer: 'MEDIA', color: '#3388ff', items: ['GDELT (deep archive)', 'GNews (curated)', 'Google News RSS (free fallback)'], desc: 'Global news monitoring' },
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
        <h2 className="text-2xl font-bold mb-8 text-center font-['Instrument_Sans',sans-serif]">Measure</h2>
        <p className="text-gray-400 text-center mb-8 max-w-xl mx-auto">
          The 9-axis behavioral radar computes a unique digital fingerprint. Each axis independently measures
          a dimension of the target's online presence.
        </p>
        <div className="grid md:grid-cols-3 gap-3">
          {[
            { axis: 'accounts', color: '#00ff88', desc: 'Number of online accounts', sources: 'Holehe, scraper engine, social enricher' },
            { axis: 'platforms', color: '#3388ff', desc: 'Diversity of platform types', sources: 'Social, dev, gaming, professional' },
            { axis: 'email_age', color: '#ffcc00', desc: 'How long the email has existed', sources: 'Breach dates, archive snapshots' },
            { axis: 'breaches', color: '#ff2244', desc: 'Breach exposure count', sources: 'HIBP, LeakCheck, IntelX' },
            { axis: 'username_reuse', color: '#ff8800', desc: 'Same username across sites', sources: 'Cross-platform matching' },
            { axis: 'data_leaked', color: '#cc88ff', desc: 'Volume of exposed data', sources: 'Breach content analysis' },
            { axis: 'geo_spread', color: '#00ddcc', desc: 'Geographic distribution', sources: 'GeoIP, user-reported locations' },
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
              separated from mail server IP locations. 30+ countries, 20+ cities — zero API calls.
            </p>
            <p className="text-sm text-gray-500 mb-3">
              GeoIP tells you where Google's servers are. xpose tells you where the <span className="text-[#00ddcc]">person</span> is.
            </p>
            <p className="text-sm text-gray-500">
              The workspace-wide geographic map gives CISOs instant visibility into their team's
              global digital exposure.
            </p>
          </div>
        </div>
      </div>
    </Section>
  )
}
