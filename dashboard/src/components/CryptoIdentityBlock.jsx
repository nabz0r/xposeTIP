import { motion } from 'framer-motion'

// S246 — Unified cryptographic-identity block: surfaces GPG findings
// (this sprint, indicator_type==="public_key") AND SSH findings (S245,
// modules github_ssh_keys / gitlab_ssh_keys). Silent return when none —
// same posture as BFPSubstrateBlock.

const SSH_MODULES = ['github_ssh_keys', 'gitlab_ssh_keys']

function classify(f) {
  const isGpg = f.indicator_type === 'public_key' || f.module === 'gpg_keys'
  const type = isGpg ? 'GPG' : 'SSH'
  const source =
    f.module === 'github_ssh_keys' ? 'GitHub' :
    f.module === 'gitlab_ssh_keys' ? 'GitLab' :
    f.module === 'gpg_keys' ? 'keys.openpgp.org' :
    (f.data?.source || '—')
  return { isGpg, type, source }
}

export default function CryptoIdentityBlock({ findings = [] }) {
  const keys = findings.filter(
    (f) => f.indicator_type === 'public_key' || SSH_MODULES.includes(f.module) || f.module === 'gpg_keys'
  )
  if (keys.length === 0) return null

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, amount: 0.3 }}
      transition={{ duration: 0.4 }}
      className="mt-6"
    >
      <h3 className="text-xs font-semibold uppercase tracking-wider text-gray-500 mb-3">
        Cryptographic Identity ({keys.length})
      </h3>
      <div className="grid gap-3 sm:grid-cols-2">
        {keys.map((f, i) => {
          const { isGpg, type, source } = classify(f)
          const accent = isGpg ? '#aa66ff' : '#3388ff'
          const fp = f.data?.fingerprint_display || f.data?.fingerprint
          const linked = f.data?.linked_emails || []
          // SSH detail: S245 stores the algorithm via scraper_engine's
          // `extracted` envelope. Read defensively across both shapes,
          // fall back to the finding title.
          const sshDetail =
            f.data?.extracted?.key_algo ||
            f.data?.key_algo ||
            f.data?.algorithm ||
            f.data?.matched ||
            f.title
          return (
            <div
              key={f.id || i}
              className="rounded-lg border border-[#1e1e2e] bg-[#12121a] p-3"
            >
              <div className="flex items-center justify-between mb-2">
                <span
                  className="text-[10px] font-mono font-semibold px-1.5 py-0.5 rounded"
                  style={{ color: accent, border: `1px solid ${accent}55` }}
                >
                  {type}
                </span>
                <span className="text-[10px] text-gray-500">{source}</span>
              </div>

              {isGpg ? (
                <div className="space-y-1">
                  {fp ? (
                    <div className="text-[11px] font-mono text-gray-300 break-all">{fp}</div>
                  ) : (
                    <div className="text-[11px] text-gray-500">fingerprint unavailable</div>
                  )}
                  {linked.length > 0 && (
                    <div className="text-[11px] text-gray-400">
                      <span style={{ color: '#00ff88' }}>{linked.length}</span> linked email
                      {linked.length > 1 ? 's' : ''}: {linked.slice(0, 3).join(', ')}
                      {linked.length > 3 ? '…' : ''}
                    </div>
                  )}
                </div>
              ) : (
                <div className="text-[11px] font-mono text-gray-300 break-all">{sshDetail}</div>
              )}
            </div>
          )
        })}
      </div>
    </motion.div>
  )
}
