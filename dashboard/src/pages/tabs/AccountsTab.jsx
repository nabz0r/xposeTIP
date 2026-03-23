import React from 'react'
import { ExternalLink, Link2, Unlink, Radar } from 'lucide-react'

const NON_SOCIAL = ['lastpass', 'office365', '1password', 'bitwarden', 'dashlane', 'keepass', 'nordpass', 'firefox', 'chrome', 'safari', 'edge', 'opera', 'eventbrite', 'booking']

export default function AccountsTab({ id, socialFindings, accounts, setAccounts, auditingAccount, setAuditingAccount, toast, setToast, load, startOAuth, auditAccount, disconnectAccount }) {
  const filteredSocialFindings = socialFindings.filter(f => {
    const d = f.data || {}
    const platform = (d.platform || d.scraper || f.title?.split(' on ')?.pop() || f.module || '').toLowerCase()
    return !NON_SOCIAL.some(ns => platform.includes(ns))
  })

  return (
    <div className="space-y-6">
      {/* Detected Social Accounts */}
      {filteredSocialFindings.length > 0 && (
        <div>
          <h3 className="text-xs font-semibold uppercase tracking-wider text-gray-500 mb-3">
            Detected Accounts ({filteredSocialFindings.length})
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
            {filteredSocialFindings.map((f, i) => {
              const d = f.data || {}
              const platform = d.platform || d.scraper || f.title?.split(' on ')?.pop() || f.module
              const username = d.username || d.display_name || f.indicator_value || ''
              const avatar = d.avatar_url || d.avatar || d.profile_image || null
              const url = f.url || d.profile_url || null

              return (
                <div key={i} className="bg-[#12121a] border border-[#1e1e2e] rounded-xl p-3 hover:border-[#00ff88]/20 transition-colors">
                  <div className="flex items-center gap-3">
                    {avatar ? (
                      <img src={avatar} alt="" className="w-8 h-8 rounded-full object-cover" />
                    ) : (
                      <div className="w-8 h-8 rounded-full bg-[#3388ff]/15 flex items-center justify-center text-[#3388ff] text-xs font-bold">
                        {(platform || '?')[0]?.toUpperCase()}
                      </div>
                    )}
                    <div className="flex-1 min-w-0">
                      <div className="text-sm font-medium truncate capitalize">{platform?.replace(/_/g, ' ')}</div>
                      {username && <div className="text-xs text-gray-500 font-mono truncate">@{username}</div>}
                    </div>
                    {url && (
                      <a href={url} target="_blank" rel="noopener noreferrer" className="text-gray-500 hover:text-[#00ff88] transition-colors">
                        <ExternalLink className="w-3.5 h-3.5" />
                      </a>
                    )}
                  </div>
                  <div className="mt-2 flex items-center gap-2">
                    <div className="flex-1 h-1 bg-[#1e1e2e] rounded-full">
                      <div className="h-1 bg-[#00ff88] rounded-full" style={{ width: `${(f.confidence || 0.5) * 100}%` }} />
                    </div>
                    <span className="text-[10px] text-gray-600">{Math.round((f.confidence || 0.5) * 100)}%</span>
                  </div>
                </div>
              )
            })}
          </div>
        </div>
      )}

      {/* OAuth Audit Section */}
      <div>
        <h3 className="text-xs font-semibold uppercase tracking-wider text-gray-500 mb-3">
          OAuth Audit
        </h3>
      <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold text-gray-300">Connected Accounts</h3>
        <div className="flex gap-2">
          {['google', 'microsoft'].map(provider => (
            <button
              key={provider}
              onClick={async () => {
                try {
                  const redirectUri = `${window.location.origin}/oauth/callback`
                  const res = await startOAuth({ provider, target_id: id, redirect_uri: redirectUri })
                  window.open(res.auth_url, '_blank', 'width=500,height=600')
                } catch (err) {
                  setToast({ type: 'error', message: err.message })
                  setTimeout(() => setToast(null), 5000)
                }
              }}
              className="inline-flex items-center gap-2 text-xs px-3 py-1.5 rounded-lg bg-[#12121a] border border-[#1e1e2e] hover:border-[#00ff88]/30 text-gray-300 hover:text-white transition-colors"
            >
              <Link2 className="w-3 h-3" />
              Connect {provider.charAt(0).toUpperCase() + provider.slice(1)}
            </button>
          ))}
        </div>
      </div>

      {accounts.length === 0 ? (
        <div className="bg-[#12121a] border border-[#1e1e2e] rounded-xl p-12 text-center">
          <Link2 className="w-12 h-12 text-gray-600 mx-auto mb-3" />
          <h3 className="text-lg font-medium text-gray-300">No connected accounts</h3>
          <p className="text-sm text-gray-500 mt-1 mb-4">
            Connect Google or Microsoft accounts to audit third-party app access, login devices, and permissions.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {accounts.map(acc => (
            <div key={acc.id} className="bg-[#12121a] border border-[#1e1e2e] rounded-xl p-4 hover:border-[#00ff88]/20 transition-colors">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                  <span className="text-sm font-semibold capitalize">{acc.provider}</span>
                  {acc.email && <span className="text-xs text-gray-400 font-mono">{acc.email}</span>}
                </div>
                <button
                  onClick={async () => {
                    if (confirm('Disconnect this account?')) {
                      await disconnectAccount(acc.id)
                      setAccounts(prev => prev.filter(a => a.id !== acc.id))
                    }
                  }}
                  className="text-gray-500 hover:text-[#ff2244] transition-colors"
                >
                  <Unlink className="w-3.5 h-3.5" />
                </button>
              </div>
              <div className="flex items-center gap-3 text-xs text-gray-500 mb-3">
                {acc.scopes?.length > 0 && <span>{acc.scopes.length} scopes</span>}
                {acc.last_audited && <span>Last audit: {new Date(acc.last_audited).toLocaleDateString()}</span>}
                <span>Connected: {new Date(acc.created_at).toLocaleDateString()}</span>
              </div>
              <button
                onClick={async () => {
                  setAuditingAccount(acc.id)
                  try {
                    const res = await auditAccount(acc.id)
                    setToast({ type: 'success', message: `Audit completed — ${res.findings_count} findings` })
                    setTimeout(() => setToast(null), 5000)
                    load()
                  } catch (err) {
                    setToast({ type: 'error', message: err.message })
                    setTimeout(() => setToast(null), 5000)
                  } finally {
                    setAuditingAccount(null)
                  }
                }}
                disabled={auditingAccount === acc.id}
                className="inline-flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-lg bg-[#00ff88]/10 text-[#00ff88] hover:bg-[#00ff88]/20 transition-colors disabled:opacity-50"
              >
                <Radar className="w-3 h-3" />
                {auditingAccount === acc.id ? 'Auditing...' : 'Run Audit'}
              </button>
            </div>
          ))}
        </div>
      )}
      </div>
      </div>
    </div>
  )
}
