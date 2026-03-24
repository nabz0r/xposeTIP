import { Radar, ArrowRight } from 'lucide-react'

export default function ScanForm({ email, setEmail, loading, error, onSubmit }) {
  return (
    <div>
      <form onSubmit={onSubmit} className="flex gap-3 max-w-md">
        <input
          type="email"
          value={email}
          onChange={e => setEmail(e.target.value)}
          placeholder="you@email.com"
          className="flex-1 bg-[#12121a] border border-[#1e1e2e] rounded-lg px-4 py-3.5 text-sm focus:outline-none focus:border-[#00ff88]/50 font-mono placeholder-gray-600 transition-colors"
        />
        <button
          type="submit"
          disabled={loading}
          className="bg-[#00ff88] text-black font-semibold rounded-lg px-6 py-3.5 text-sm hover:bg-[#00ff88]/90 disabled:opacity-50 flex items-center gap-2 transition-all group"
        >
          {loading ? (
            <Radar className="w-4 h-4 animate-spin" />
          ) : (
            <>
              Scan now
              <ArrowRight className="w-3.5 h-3.5 group-hover:translate-x-0.5 transition-transform" />
            </>
          )}
        </button>
      </form>
      {error && <p className="text-xs text-[#ff2244] mt-2">{error}</p>}
    </div>
  )
}
