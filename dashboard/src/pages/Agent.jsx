import { Link } from 'react-router-dom'
import Section from '../components/shared/Section'
import AgentClusterDiagram from '../components/agent/AgentClusterDiagram'

// S302b — /doc/agent. Public concept explainer (decision A): the AI-agent identity
// vision with an ILLUSTRATIVE diagram. No live data, no API call — the real AgentNetwork
// viz stays auth-gated + workspace-kind-gated at /agent-network. Representative public
// agent names only. BFP's network-layer identity, made concrete.

const BUCKETS = [
  ['shared', '#185FA5', 'Shared CDN', 'Cloudflare · Fastly · Akamai — the super-hub. Most agents route through shared CDN, so it absorbs the bulk of agent traffic.'],
  ['own', '#0F6E56', 'Own ASN / hyperscaler', 'Google, Amazon, Microsoft and other operators running their own network — the agent operates from infrastructure it controls.'],
  ['foreign', '#993C1D', 'Foreign network', 'An agent routing from a network outside its nominal operator — the outlier that stands apart from the hyperscaler islands.'],
  ['host', '#5F5E5A', '3rd-party host', 'Hurricane Electric, OVH, Hetzner and similar — rented infrastructure, neither shared CDN nor first-party.'],
]

export default function Agent() {
  return (
    <div className="pb-20">
      {/* Hero */}
      <Section className="py-20">
        <div className="max-w-5xl mx-auto px-6 text-center">
          <h1 className="text-4xl md:text-5xl font-bold mb-4 font-['Instrument_Sans',sans-serif]">
            AI <span className="text-[#00ff88]">Agents</span>
          </h1>
          <p className="text-lg text-gray-400 max-w-2xl mx-auto">
            Agents leak an identity too — not a face, a <span className="text-white">place</span>.
            Humans cluster by behavioral fingerprint; agents cluster by where they operate from.
          </p>
        </div>
        <AgentClusterDiagram />
        <p className="text-center text-xs text-gray-600 font-mono max-w-xl mx-auto px-6">
          Illustrative — representative public agents. The live corpus view is operator-only.
        </p>
      </Section>

      {/* §1 — The Place axis */}
      <Section className="py-16 bg-[#0d0d14]">
        <div className="max-w-4xl mx-auto px-6">
          <h2 className="text-2xl font-bold mb-2 font-['Instrument_Sans',sans-serif]">1 · The Place axis</h2>
          <p className="text-gray-400 max-w-3xl mb-6 leading-relaxed">
            An AI agent&apos;s identity, in our system, isn&apos;t a face — it&apos;s a network footprint.
            You rarely see <span className="text-white">who</span> an agent is, but you can see
            {' '}<span className="text-white">where it operates from</span> — and that&apos;s enough to cluster it.
          </p>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {[['operator', 'who runs it'], ['ASN', 'the network it routes through'], ['IP', 'the address it speaks from'], ['country', 'where that network sits']].map(([k, v]) => (
              <div key={k} className="bg-[#12121a] border border-[#1e1e2e] rounded-xl p-4">
                <div className="font-mono text-sm text-[#00ff88] mb-1">{k}</div>
                <div className="text-sm text-gray-400">{v}</div>
              </div>
            ))}
          </div>
          <p className="text-gray-500 text-sm max-w-3xl mt-6 leading-relaxed">
            This is the agent-side complement to the human behavioral axes: a person leaks a clusterable
            identity through behavior and OSINT; an agent leaks one through its network coordinates.
          </p>
        </div>
      </Section>

      {/* §2 — Clustering */}
      <Section className="py-16">
        <div className="max-w-4xl mx-auto px-6">
          <h2 className="text-2xl font-bold mb-2 font-['Instrument_Sans',sans-serif]">2 · Clustering</h2>
          <p className="text-gray-400 max-w-3xl mb-8 leading-relaxed">
            Agents cluster by operator ASN — and <span className="text-white">Cloudflare emerges as the natural
            super-hub</span>, because shared CDN absorbs most agent traffic. This is the agent equivalent of the
            BFP behavioral cluster: the same identity-at-scale property, applied to non-human actors. Four buckets:
          </p>
          <div className="grid md:grid-cols-2 gap-4">
            {BUCKETS.map(([key, color, title, body]) => (
              <div key={key} className="bg-[#12121a] border border-[#1e1e2e] rounded-xl p-5 flex gap-4">
                <span className="w-3 h-3 rounded-full shrink-0 mt-1.5" style={{ background: color }} />
                <div>
                  <div className="text-sm font-semibold text-white mb-1">{title}</div>
                  <div className="text-sm text-gray-400 leading-relaxed">{body}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </Section>

      {/* §3 — Declared vs known */}
      <Section className="py-16 bg-[#0d0d14]">
        <div className="max-w-4xl mx-auto px-6">
          <h2 className="text-2xl font-bold mb-2 font-['Instrument_Sans',sans-serif]">3 · Declared vs known</h2>
          <p className="text-gray-400 max-w-3xl mb-8 leading-relaxed">
            The honesty gradient — the same epistemics as the rest of the stack: <span className="text-white">assertion
            beats inference</span>.
          </p>
          <div className="grid md:grid-cols-2 gap-4">
            <div className="rounded-xl border border-[#9bcc3a]/40 bg-[#9bcc3a]/[0.05] p-5">
              <div className="flex items-center gap-2 mb-2">
                <span className="w-3 h-3 rounded-full border-2 border-[#9bcc3a]" />
                <span className="text-sm font-semibold text-white">Declared — signed (Web Bot Auth)</span>
              </div>
              <p className="text-sm text-gray-400 leading-relaxed">
                The agent cryptographically signs its requests via <span className="font-mono">Web Bot Auth (WBA)</span>,
                presenting a verifiable, operator-asserted identity. This is the ceiling — exactly like
                {' '}<span className="font-mono">operator-asserted = 100%</span> in the scoring engine.
              </p>
            </div>
            <div className="rounded-xl border border-[#1e1e2e] bg-[#12121a] p-5">
              <div className="flex items-center gap-2 mb-2">
                <span className="w-3 h-3 rounded-full border border-gray-500" />
                <span className="text-sm font-semibold text-white">Known — inferred</span>
              </div>
              <p className="text-sm text-gray-400 leading-relaxed">
                No signature. The agent&apos;s identity is <span className="text-white">inferred</span> from its
                network coordinates (UA + ASN + IP) — corroboration, not assertion. Strong, but never the ceiling.
              </p>
            </div>
          </div>
        </div>
      </Section>

      {/* §4 — Why it matters */}
      <Section className="py-16">
        <div className="max-w-4xl mx-auto px-6">
          <h2 className="text-2xl font-bold mb-2 font-['Instrument_Sans',sans-serif]">4 · Why it matters</h2>
          <p className="text-gray-400 max-w-3xl mb-6 leading-relaxed">
            This is BFP&apos;s <span className="text-white">network-layer identity</span> vision — ASN and network
            signatures as a path to unicity — made observable <span className="text-white">today</span>, because
            agents announce themselves: a public user-agent, routed through an identifiable ASN. We observe an
            agent&apos;s own announced, network-level identity — not people, not surveillance. Identity belongs in
            the stack — for agents too.
          </p>
          <div className="border-t border-[#1e1e2e] pt-8 flex flex-wrap gap-x-8 gap-y-3">
            <Link to="/doc/bfp" className="text-[#00ff88] hover:underline text-sm font-mono">The BFP protocol →</Link>
            <Link to="/doc/engine" className="text-[#00ff88] hover:underline text-sm font-mono">How scoring works →</Link>
          </div>
        </div>
      </Section>
    </div>
  )
}
