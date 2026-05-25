/**
 * S226 — Visualization Layer section on /architecture.
 *
 * Surfaces the two-tier identity visualization shipped in S136 (GenerativeAvatar)
 * + S219-S222b (PixelCat + behavioral cluster). Sits between BFPLayer and
 * ScraperBreakdown.
 *
 * Style raccord palette S204-S207 (#00ff88 / #3388ff / #ff5588 / #888 + grays),
 * framer-motion whileInView once-only amount:0.3, fontSize ≥11.
 */

import { motion } from 'framer-motion'
import Section from '../shared/Section'
import GenerativeAvatar from '../GenerativeAvatar'
import PixelCat from '../PixelCat'

const fadeInUp = (delay = 0) => ({
  initial: { opacity: 0, y: 16 },
  whileInView: { opacity: 1, y: 0 },
  viewport: { once: true, amount: 0.3 },
  transition: { delay, duration: 0.5 },
})

// Demo seeds (deterministic) for the two-tier showcase
const DEMO_AVATAR_SEED = {
  email_hash: 4824,
  hue: 142,
  num_points: 7,
  rotation: 213,
}

// Sample behavioral hash for PixelCat demo — drives detail layer:
// pattern=calico, accessory=badge, marking=none, expression=chill
const DEMO_BFP_HASH = '14e0de8400000000abcdef1234567890fedcba0987654321'

// Three identical cats for the cluster row (same seed + same hash = same cat)
const CLUSTER_SEED = {
  email_hash: 9213,
  hue: 38,
  num_points: 4,
  rotation: 89,
}
const CLUSTER_BFP_HASH = 'f9a5400a00000000abcdef1234567890fedcba0987654321'

export default function VisualizationLayer() {
  return (
    <Section className="py-32 bg-[#0a0a0f]">
      <div className="max-w-5xl mx-auto px-6">
        {/* Header */}
        <motion.div {...fadeInUp(0)} className="text-center mb-16">
          <div className="inline-block text-[10px] font-mono text-[#3388ff] bg-[#3388ff]/10 px-2 py-0.5 rounded-full mb-3">
            LAYER — VISUALIZATION
          </div>
          <h2 className="text-3xl md:text-4xl font-bold mb-4 font-['Instrument_Sans',sans-serif]">
            Identity, made visible
          </h2>
          <p className="text-gray-400 max-w-xl mx-auto leading-relaxed">
            Every identity gets two visual representations — both derived from
            the same fingerprint, neither requires manual input.
          </p>
        </motion.div>

        {/* Two-tier visualization */}
        <div className="grid md:grid-cols-2 gap-8 mb-16">
          {/* Human avatar tier */}
          <motion.div {...fadeInUp(0.1)} className="bg-[#12121a] border border-[#1e1e2e] rounded-xl p-6 flex flex-col items-center text-center">
            <div className="mb-4">
              <GenerativeAvatar seed={DEMO_AVATAR_SEED} size={120} score={45} />
            </div>
            <div className="text-xs font-mono text-[#00ff88] mb-2">FACE — 14 axes</div>
            <div className="text-2xl font-bold mb-1 font-['Instrument_Sans',sans-serif]">5.4B combos</div>
            <p className="text-sm text-gray-400 leading-relaxed">
              CryptoPunk-style 32×32 pixel face. Skin tone, eyes, hair, expression,
              accessory — all derived from the identity fingerprint seed.
              Score-reactive: expression shifts with exposure.
            </p>
          </motion.div>

          {/* Behavioral cat tier */}
          <motion.div {...fadeInUp(0.2)} className="bg-[#12121a] border border-[#1e1e2e] rounded-xl p-6 flex flex-col items-center text-center">
            <div className="mb-4 py-3">
              <PixelCat
                seed={DEMO_AVATAR_SEED}
                behavioralHash={DEMO_BFP_HASH}
                pose="idle"
                size={120}
                animated={false}
              />
            </div>
            <div className="text-xs font-mono text-[#ff5588] mb-2">CAT — 4 silhouette axes + 4 behavioral axes</div>
            <div className="text-2xl font-bold mb-1 font-['Instrument_Sans',sans-serif]">920K combos</div>
            <p className="text-sm text-gray-400 leading-relaxed">
              Silhouette stable per email (fur, eyes, collar). Pattern + accessory +
              marking + expression revealed post-scan from the BFP behavioral hash.
              Same cat = behaviorally similar identity.
            </p>
          </motion.div>
        </div>

        {/* Behavioral cluster row */}
        <motion.div {...fadeInUp(0.3)} className="bg-[#0d0d14] border border-[#1e1e2e] rounded-xl p-6">
          <div className="flex items-center gap-3 mb-4">
            <div className="text-xs font-mono text-[#3388ff]">BEHAVIORAL CLUSTER · K=3</div>
            <div className="h-px flex-1 bg-[#1e1e2e]"/>
          </div>
          <div className="flex items-center justify-center gap-8 py-4 flex-wrap">
            {[0, 1, 2].map((i) => (
              <div key={i} className="flex flex-col items-center">
                <PixelCat
                  seed={CLUSTER_SEED}
                  behavioralHash={CLUSTER_BFP_HASH}
                  pose="idle"
                  size={64}
                  animated={false}
                />
                <div className="text-[10px] font-mono text-gray-500 mt-2">peer #{i + 1}</div>
              </div>
            ))}
          </div>
          <p className="text-sm text-gray-400 text-center max-w-2xl mx-auto mt-4 leading-relaxed">
            Targets sharing a behavioral hash prefix render the same cat. This is
            the K=3 clustering of <span className="text-white">behavioral_hash_v1</span> made
            observable — by design, not by accident.
          </p>
        </motion.div>
      </div>
    </Section>
  )
}
