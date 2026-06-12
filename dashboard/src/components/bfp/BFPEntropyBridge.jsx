import { motion } from 'framer-motion'

// S277 — BFPEntropyBridge on /bfp, inserted between BFPArchitecture and
// BFPCryptography. Makes the major post-S232 fact exist on the page: the BFP
// substrate gained its first quantitative consumer — H(cluster) turns the
// behavioral hash into bits of the entropy ledger (S271). Bare div (Section +
// bg wrapper provided by BFP.jsx, like the other bfp/ components). Blue
// 'measurement' badge raccord EntropyLayer (S276). Diagram is 100% illustrative.

export default function BFPEntropyBridge() {
  return (
    <div className="max-w-5xl mx-auto px-6">
      <div className="max-w-3xl mx-auto text-center mb-12">
        <div className="inline-block text-[10px] font-mono text-[#3388ff] bg-[#3388ff]/10 px-2 py-0.5 rounded-full mb-3">
          SUBSTRATE → BITS
        </div>
        <h2 className="text-3xl md:text-4xl font-bold mb-4 font-['Instrument_Sans',sans-serif]">
          H(cluster) — the hash becomes bits
        </h2>
        <p className="text-gray-400 mb-4 leading-relaxed">
          The behavioral hash groups identities into buckets — K=3 locality-sensitive
          clustering over the 11 axes. Until now it answered one question:{' '}
          <span className="text-white">who belongs together</span>.
        </p>
        <p className="text-gray-400 mb-4 leading-relaxed">
          The entropy engine closes the loop. A bucket's share of the corpus is a
          probability — and a probability is bits:{' '}
          <span className="font-mono text-[#00ff88]">−log2(bucket / corpus)</span>.
          Belonging to a tight bucket carries real identifying power; belonging to a
          crowded, info-starved bucket carries almost none. The cold-start bucket is
          honest by design: it dilutes as the corpus grows.
        </p>
        <p className="text-sm text-gray-500 leading-relaxed">
          The hash stays what it is — a clustering primitive, never a unique
          identifier. H(cluster) just measures how much that clustering reveals, and
          feeds it into the per-target bits ledger alongside country, provider, and name.
        </p>
      </div>

      <div className="max-w-xl mx-auto">
        <BridgeDiagram />
      </div>

      <div className="mt-8 text-center">
        <a
          href="/architecture"
          className="inline-flex items-center gap-2 text-[#3388ff] hover:text-[#3388ff]/80 text-sm font-mono transition-colors"
        >
          How the full ledger works →
        </a>
      </div>
    </div>
  )
}

function BridgeDiagram() {
  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, amount: 0.3 }}
      transition={{ duration: 0.6 }}
    >
      <svg
        viewBox="0 0 600 400"
        className="w-full max-w-md mx-auto h-auto"
        xmlns="http://www.w3.org/2000/svg"
      >
        <defs>
          <marker id="bridge-arr-neutral" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
            <polygon points="0 0, 6 3, 0 6" fill="#888" />
          </marker>
          <marker id="bridge-arr-blue" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
            <polygon points="0 0, 6 3, 0 6" fill="#3388ff" />
          </marker>
        </defs>

        {/* behavioral hash node (top) */}
        <rect x={210} y={24} width={180} height={34} rx={6} fill="#00ff8810" stroke="#00ff88" strokeWidth="1.5" />
        <text x={300} y={46} textAnchor="middle" fill="#00ff88" fontSize="13" fontFamily="monospace">behavioral hash</text>

        {/* arrows hash → 3 buckets */}
        <line x1={300} y1={58} x2={130} y2={116} stroke="#888" strokeWidth="1.5" markerEnd="url(#bridge-arr-neutral)" />
        <line x1={300} y1={58} x2={300} y2={146} stroke="#888" strokeWidth="1.5" markerEnd="url(#bridge-arr-neutral)" />
        <line x1={300} y1={58} x2={470} y2={171} stroke="#888" strokeWidth="1.5" markerEnd="url(#bridge-arr-neutral)" />

        {/* 3 buckets — common baseline y=220, height ∝ crowding (inverse of bits) */}
        <rect x={70} y={120} width={120} height={100} rx={6} fill="#888888" opacity={0.4} stroke="#888" strokeWidth="1.5" />
        <rect x={245} y={150} width={110} height={70} rx={6} fill="#3388ff" opacity={0.85} />
        <rect x={420} y={175} width={100} height={45} rx={6} fill="#00ff88" opacity={0.85} />

        {/* bucket labels */}
        <text x={130} y={240} textAnchor="middle" fill="#aaa" fontSize="11" fontFamily="monospace">crowded bucket</text>
        <text x={130} y={256} textAnchor="middle" fill="#888" fontSize="11" fontFamily="monospace">≈ 0–1 bits</text>
        <text x={300} y={240} textAnchor="middle" fill="#aaa" fontSize="11" fontFamily="monospace">mid bucket</text>
        <text x={300} y={256} textAnchor="middle" fill="#3388ff" fontSize="11" fontFamily="monospace">≈ 4 bits</text>
        <text x={470} y={240} textAnchor="middle" fill="#aaa" fontSize="11" fontFamily="monospace">tight bucket</text>
        <text x={470} y={256} textAnchor="middle" fill="#00ff88" fontSize="11" fontFamily="monospace">≈ 7 bits</text>

        {/* single arrow → bits ledger */}
        <line x1={300} y1={266} x2={300} y2={300} stroke="#3388ff" strokeWidth="1.5" markerEnd="url(#bridge-arr-blue)" />

        {/* bits ledger box */}
        <rect x={205} y={302} width={190} height={44} rx={6} fill="#3388ff10" stroke="#3388ff" strokeWidth="1.5" />
        <text x={300} y={322} textAnchor="middle" fill="#3388ff" fontSize="12" fontFamily="monospace">bits ledger</text>
        <text x={300} y={338} textAnchor="middle" fill="#888" fontSize="11" fontFamily="monospace">the belonging term</text>

        {/* legend */}
        <text x={300} y={376} textAnchor="middle" fill="#888" fontSize="11" fontFamily="monospace">
          Illustrative — real values are per-target
        </text>
      </svg>
    </motion.div>
  )
}
