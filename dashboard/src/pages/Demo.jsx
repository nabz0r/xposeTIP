import { useEffect, useMemo, useRef, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Check, ShieldCheck } from 'lucide-react'
import demoProfile from '../data/demoProfile.json'
import { ACTS, PACE, buildTimeline } from '../lib/demoScript'
import DemoFlow from '../components/DemoFlow'
import PixelCat, { phaseFromScan } from '../components/PixelCat'
import DemoAvatar from '../components/DemoAvatar'
import FingerprintRadar from '../components/FingerprintRadar'
import CryptoIdentityBlock from '../components/CryptoIdentityBlock'
import { SOURCE_COUNT } from '../components/landing/constants'

// S249 — Live Demo page. Public route, zero network during pitch.
// Scripted replay over a frozen profile snapshot. The fakeScan state moves
// through 5 acts → phaseFromScan() picks the PixelCat pose; activeLayer
// drives the DemoFlow backdrop; status stream interleaves real + flavor.

export default function Demo() {
  const [actIdx, setActIdx] = useState(0)
  const [fakeScan, setFakeScan] = useState(ACTS[0].fakeScan)
  const [activeLayer, setActiveLayer] = useState(ACTS[0].activeLayer)
  const [statuses, setStatuses] = useState([])
  const [revealed, setRevealed] = useState(false)
  const [consentVerified, setConsentVerified] = useState(false)
  const [running, setRunning] = useState(false)
  const [pace, setPace] = useState(PACE)
  const timersRef = useRef([])
  const streamRef = useRef(null)

  const beats = useMemo(() => buildTimeline(demoProfile, pace), [pace])
  const totalDur = useMemo(() => beats.reduce((m, b) => Math.max(m, b.tMs), 0), [beats])

  const pose = phaseFromScan(fakeScan)
  const cluster = demoProfile.cluster || {}
  const target = demoProfile.target || {}
  const profile = demoProfile.profile || {}
  const counts = demoProfile.counts || {}

  function reset() {
    timersRef.current.forEach(clearTimeout)
    timersRef.current = []
    setActIdx(0)
    setFakeScan(ACTS[0].fakeScan)
    setActiveLayer(ACTS[0].activeLayer)
    setStatuses([])
    setRevealed(false)
    setConsentVerified(false)
    setRunning(false)
  }

  function start() {
    reset()
    setRunning(true)
    beats.forEach((b) => {
      const id = setTimeout(() => applyBeat(b), b.tMs)
      timersRef.current.push(id)
    })
  }

  function applyBeat(b) {
    if (b.type === 'act') {
      setActIdx(b.payload.index)
      setFakeScan(b.payload.act.fakeScan)
    } else if (b.type === 'layer') {
      setActiveLayer(b.payload.layer)
    } else if (b.type === 'status') {
      setStatuses((s) => [...s.slice(-9), b.payload])
    } else if (b.type === 'reveal') {
      setRevealed(true)
      setRunning(false)
    }
  }

  // Cleanup timers on unmount or restart
  useEffect(() => () => timersRef.current.forEach(clearTimeout), [])

  // Auto-scroll the status stream
  useEffect(() => {
    if (streamRef.current) streamRef.current.scrollTop = streamRef.current.scrollHeight
  }, [statuses.length])

  const currentAct = ACTS[actIdx]

  return (
    <div className="min-h-screen bg-[#0a0a0f] text-white overflow-x-hidden">
      <style>{`
        @keyframes pulseBorder {
          0%, 100% { box-shadow: 0 0 0 0 rgba(0,255,136,0); }
          50% { box-shadow: 0 0 0 6px rgba(0,255,136,0.18); }
        }
      `}</style>

      <header className="px-6 py-5 flex items-center justify-between border-b border-[#1e1e2e]">
        <div className="flex items-center gap-3">
          <ShieldCheck className="w-5 h-5 text-[#00ff88]" />
          <span className="font-bold text-sm tracking-wider">xposeTIP · Live Demo</span>
        </div>
        <div className="flex items-center gap-3 text-xs font-mono text-gray-500">
          <label className="hidden md:flex items-center gap-2">
            Pace
            <input
              type="range"
              min={0.6}
              max={2.0}
              step={0.1}
              value={pace}
              onChange={(e) => setPace(Number(e.target.value))}
              className="accent-[#00ff88] w-24"
              disabled={running}
            />
            <span className="w-8 text-right">×{pace.toFixed(1)}</span>
          </label>
          <button
            type="button"
            onClick={running ? reset : start}
            className={`px-3 py-1.5 rounded font-mono text-xs border transition-colors ${
              running
                ? 'border-gray-600 text-gray-300 hover:bg-[#1e1e2e]'
                : 'border-[#00ff88]/50 text-[#00ff88] hover:bg-[#00ff88]/10'
            }`}
          >
            {running ? 'Reset' : revealed ? 'Replay' : 'Start scan'}
          </button>
        </div>
      </header>

      {/* ─── Main stage ─────────────────────────────────────────── */}
      {!revealed && (
        <div className="grid md:grid-cols-[1fr_360px] gap-6 px-6 py-6">
          {/* Left — DemoFlow backdrop + PixelCat overlay */}
          <div className="relative bg-[#0d0d14] border border-[#1e1e2e] rounded-xl p-4 min-h-[480px] overflow-hidden">
            <DemoFlow activeLayer={activeLayer} sources={SOURCE_COUNT} scanners={28} />

            {/* PixelCat overlay — Matrix-scramble avatar driven by act phase.
                Scramble during acts 1-3 → zone-resolve during act 4 (Profiling,
                the hash-injection moment) → clean by act 5. */}
            <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 z-10">
              <DemoAvatar
                seed={target.fingerprint_avatar_seed}
                behavioralHash={target.bfp_behavioral_hash_v1}
                pose={pose}
                size={140}
                phase={
                  revealed ? 'resolved'
                  : actIdx < 3 ? 'scramble'
                  : actIdx === 3 ? 'resolving'
                  : 'resolved'
                }
                resolveMs={ACTS[3].durationMs * pace}
              />
            </div>

            {/* Act ticker — bottom-left of stage */}
            <div className="absolute bottom-4 left-4 right-4 flex items-center gap-3 text-xs font-mono">
              <span className="text-gray-500 uppercase tracking-wider shrink-0">{currentAct.title}</span>
              <span className="text-gray-400 truncate">{currentAct.pitch}</span>
              <span className="ml-auto text-gray-600">
                pose: <span style={{ color: currentAct.accent }}>{pose}</span>
              </span>
            </div>
          </div>

          {/* Right — Status stream + counters */}
          <div className="flex flex-col gap-4">
            <div className="bg-[#0d0d14] border border-[#1e1e2e] rounded-xl p-4">
              <div className="text-[11px] uppercase tracking-wider text-gray-500 font-mono mb-2">Status stream</div>
              <div
                ref={streamRef}
                className="h-[300px] overflow-y-auto font-mono text-[11px] leading-relaxed pr-2"
              >
                {statuses.length === 0 && (
                  <div className="text-gray-600">Press <span className="text-[#00ff88]">Start scan</span> to begin.</div>
                )}
                {statuses.map((s, i) => (
                  <div
                    key={`${i}-${s.text}`}
                    className={s.kind === 'real' ? 'text-[#00ff88]' : 'text-gray-500'}
                  >
                    {s.kind === 'real' ? '› ' : '· '}{s.text}
                  </div>
                ))}
              </div>
            </div>

            {/* Counters */}
            <div className="bg-[#0d0d14] border border-[#1e1e2e] rounded-xl p-4 grid grid-cols-2 gap-3 text-xs font-mono">
              <Counter label="Findings" value={counts.total_findings ?? '—'} accent="#aaa" />
              <Counter label="Accounts" value={counts.social_accounts ?? '—'} accent="#3388ff" />
              <Counter label="Breaches" value={counts.breaches ?? '—'} accent="#ff5588" />
              <Counter label="Sources" value={counts.data_sources ?? '—'} accent="#00ff88" />
            </div>

            {/* Act dots */}
            <div className="flex items-center justify-between px-2">
              {ACTS.map((a, i) => (
                <div key={a.id} className="flex flex-col items-center gap-1">
                  <span
                    className="w-2.5 h-2.5 rounded-full transition-colors"
                    style={{ background: i <= actIdx ? a.accent : '#1e1e2e' }}
                  />
                  <span className="text-[10px] text-gray-600 font-mono">{a.title.split(' · ')[0]}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* ─── Reveal ─────────────────────────────────────────────── */}
      <AnimatePresence>
        {revealed && (
          <motion.div
            key="reveal"
            initial={{ opacity: 0, y: 24 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            className="px-6 py-10 max-w-5xl mx-auto"
          >
            {/* Header */}
            <div className="bg-[#12121a] border border-[#1e1e2e] rounded-xl p-6 mb-4 flex items-center gap-5">
              <PixelCat
                seed={target.fingerprint_avatar_seed}
                behavioralHash={target.bfp_behavioral_hash_v1}
                pose="sleep"
                size={88}
                animated={false}
              />
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-3 mb-1 flex-wrap">
                  <h1 className="text-2xl font-bold font-['Instrument_Sans',sans-serif]">
                    {target.display_name || profile.primary_name}
                  </h1>
                  {consentVerified ? (
                    <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] font-mono bg-[#00ff88]/10 text-[#00ff88] border border-[#00ff88]/30">
                      <Check className="w-3 h-3" />
                      Consent verified · google
                    </span>
                  ) : (
                    <button
                      type="button"
                      onClick={() => setConsentVerified(true)}
                      className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] font-mono bg-[#1e1e2e] text-gray-300 hover:bg-[#2a2a3e] border border-[#1e1e2e] hover:border-[#3388ff]/40 transition-colors"
                      title="Demo only — flips the badge without leaving the page."
                    >
                      Request SSO consent
                    </button>
                  )}
                </div>
                <p className="text-sm font-mono text-gray-400">{target.email}</p>
                {profile.location && (
                  <p className="text-xs text-gray-500 mt-1">{profile.location} · {profile.company}</p>
                )}
                {profile.bio && (
                  <p className="text-sm text-gray-300 mt-2 italic">"{profile.bio}"</p>
                )}
              </div>
              <div className="text-right">
                <div className="text-[10px] uppercase tracking-wider text-gray-500 font-mono">Exposure</div>
                <div className="text-3xl font-mono font-bold text-[#ff8800]">{target.exposure_score ?? '—'}</div>
                <div className="text-[10px] text-gray-600 font-mono mt-1">threat {target.threat_score ?? '—'}</div>
              </div>
            </div>

            {/* Behavioral cluster pill (inline, no network) */}
            {cluster.count > 0 && (
              <div className="bg-[#12121a] border border-[#1e1e2e] rounded-xl p-3 flex items-center gap-3 mb-4">
                <PixelCat
                  seed={target.fingerprint_avatar_seed}
                  behavioralHash={target.bfp_behavioral_hash_v1}
                  pose="idle"
                  size={20}
                  animated={false}
                />
                <span className="text-xs font-medium text-gray-300">Behavioral cluster</span>
                <span className="text-xs font-mono text-[#00ff88]">
                  {cluster.count} {cluster.count === 1 ? 'peer' : 'peers'}
                </span>
                {cluster.prefix && (
                  <span className="text-[10px] font-mono text-gray-500 hidden sm:inline">
                    hash[:16] · {cluster.prefix.slice(0, 8)}…
                  </span>
                )}
                <span className="ml-auto text-[10px] text-gray-500 hidden md:inline">
                  same PixelCat detail layer
                </span>
              </div>
            )}

            {/* Two columns: radar + cryptographic identity */}
            <div className="grid md:grid-cols-[1fr_360px] gap-4">
              <div className="bg-[#12121a] border border-[#1e1e2e] rounded-xl p-6">
                <h2 className="text-xs uppercase tracking-wider text-gray-500 mb-3 font-mono">
                  11-axis behavioral fingerprint
                </h2>
                <div className="flex justify-center">
                  <FingerprintRadar fingerprint={demoProfile.fingerprint} size="large" animate />
                </div>
              </div>

              <div className="bg-[#12121a] border border-[#1e1e2e] rounded-xl p-4">
                <h2 className="text-xs uppercase tracking-wider text-gray-500 mb-3 font-mono">
                  Email · Timezone · Languages
                </h2>
                <Row label="Email" value={profile.email_status?.status === 'true' ? '✓ Deliverable' : (profile.email_status?.status || '—')} accent="#00ff88" />
                <Row label="Provider" value={profile.email_status?.provider || '—'} />
                <Row label="Breaches" value={`${profile.breach_summary?.count ?? '—'}`} accent="#ff5588" />
                {profile.geo_consistency?.primary_country && (
                  <Row label="Country" value={`${profile.geo_consistency.primary_country} · ${Math.round((profile.geo_consistency.consistency_score || 0) * 100)}% consistent`} />
                )}
                {profile.timezone?.utc_offset !== undefined && (
                  <Row label="Timezone" value={`UTC${profile.timezone.utc_offset >= 0 ? '+' : ''}${profile.timezone.utc_offset}`} />
                )}
                {profile.languages?.primary && (
                  <Row label="Languages" value={`${profile.languages.primary.toUpperCase()} ${Math.round((profile.languages.languages?.[0]?.confidence || 0) * 100)}%`} />
                )}
                <CryptoIdentityBlock findings={demoProfile.crypto_findings || []} />
              </div>
            </div>

            <div className="text-center mt-10">
              <p className="text-sm text-gray-500 max-w-xl mx-auto leading-relaxed">
                <span className="text-[#00ff88]">The subject takes the reading back.</span>{' '}
                The internet already knew. xposeTIP returns the reading to its rightful owner — the person it describes.
              </p>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      <footer className="border-t border-[#1e1e2e] px-6 py-4 text-[10px] font-mono text-gray-600 flex items-center justify-between">
        <span>xposeTIP · scripted replay · zero network during pitch · pace ×{pace.toFixed(1)}</span>
        <span>elapsed: {Math.round(totalDur / 1000)}s · {beats.length} beats</span>
      </footer>
    </div>
  )
}

function Counter({ label, value, accent }) {
  return (
    <div className="bg-[#12121a] rounded p-2 border border-[#1e1e2e]">
      <div className="text-[10px] uppercase tracking-wider text-gray-500">{label}</div>
      <div className="text-lg font-bold mt-0.5" style={{ color: accent }}>{value}</div>
    </div>
  )
}

function Row({ label, value, accent }) {
  return (
    <div className="flex items-center justify-between py-1.5 border-b border-[#1e1e2e] last:border-0 text-xs">
      <span className="text-gray-500 font-mono">{label}</span>
      <span className="font-mono" style={{ color: accent || '#e5e7eb' }}>{value}</span>
    </div>
  )
}
