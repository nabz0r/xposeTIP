import SourcesTab from './SourcesTab'
import AccountsTab from './AccountsTab'

const SUB_TABS = [
  { key: 'sources',  label: 'Sources' },
  { key: 'accounts', label: 'Connected accounts' },
]

export default function SourcesHubTab({
  activeSub, setActiveSub, sourcesData,
  // AccountsTab props
  id, socialFindings, accounts, setAccounts, auditingAccount, setAuditingAccount,
  toast, setToast, load, startOAuth, auditAccount, disconnectAccount,
}) {
  return (
    <div className="space-y-4">
      <div className="flex flex-wrap gap-2">
        {SUB_TABS.map(t => (
          <button key={t.key} onClick={() => setActiveSub(t.key)}
            className={`px-3 py-1.5 rounded-full text-xs font-medium transition-colors ${
              activeSub === t.key
                ? 'bg-[#00ff88]/20 text-[#00ff88] border border-[#00ff88]/40'
                : 'bg-[#12121a] text-gray-400 border border-[#1e1e2e] hover:text-white'
            }`}>
            {t.label}
          </button>
        ))}
      </div>
      {activeSub === 'sources' && <SourcesTab sourcesData={sourcesData} />}
      {activeSub === 'accounts' && (
        <AccountsTab
          id={id} socialFindings={socialFindings} accounts={accounts}
          setAccounts={setAccounts} auditingAccount={auditingAccount}
          setAuditingAccount={setAuditingAccount} toast={toast} setToast={setToast}
          load={load} startOAuth={startOAuth} auditAccount={auditAccount}
          disconnectAccount={disconnectAccount}
        />
      )}
    </div>
  )
}
