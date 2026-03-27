import { useState } from 'react'
import { Camera, X } from 'lucide-react'

function getAvatarQuality(url) {
  if (!url) return 0
  const low = url.toLowerCase()
  if (low.includes('d=identicon') || low.includes('d=retro') || low.includes('d=wavatar')) return 1
  if (low.includes('redditstatic.com/avatars/defaults')) return 1
  if (low.includes('simg-ssl.duolingo.com/avatar/default')) return 1
  if (url.startsWith('//')) return 1
  if (low.includes('githubusercontent.com')) return 3
  if (low.includes('linktr.ee')) return 3
  if (low.includes('pbs.twimg.com')) return 3
  if (low.includes('googleusercontent.com')) return 3
  if (low.includes('fullcontact.com')) return 3
  return 2
}

export default function PhotosTab({ profile, target }) {
  const avatars = profile?.avatars || []
  const primaryAvatar = profile?.primary_avatar || target?.avatar_url
  const [enlarged, setEnlarged] = useState(null)

  if (!avatars.length && !primaryAvatar) {
    return (
      <div className="flex flex-col items-center justify-center h-64 text-gray-500">
        <Camera className="w-12 h-12 text-gray-600 mb-3" />
        <h3 className="text-lg font-medium text-gray-300">No profile photos collected</h3>
        <p className="text-sm text-gray-500 mt-1">Run a scan to discover profile photos across platforms.</p>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Primary photo */}
      {primaryAvatar && (
        <div>
          <h3 className="text-xs font-semibold uppercase tracking-wider text-gray-500 mb-3">
            Primary Photo
          </h3>
          <div className="flex items-center gap-4">
            <img
              src={primaryAvatar}
              alt="Primary"
              className="w-24 h-24 rounded-full object-cover border-2 border-[#00ff88]/30 shadow-[0_0_20px_rgba(0,255,136,0.1)] cursor-pointer hover:border-[#00ff88]/60 transition-colors"
              onClick={() => setEnlarged(primaryAvatar)}
              onError={(e) => { e.target.style.display = 'none' }}
            />
            <div>
              <p className="text-sm text-gray-300">Used for profile identification</p>
              <p className="text-xs text-gray-500 mt-1 font-mono">
                {avatars.find(a => a.url === primaryAvatar)?.source?.replace(/_profile|_scraper/g, '') || 'detected'}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* All discovered photos */}
      <div>
        <h3 className="text-xs font-semibold uppercase tracking-wider text-gray-500 mb-3">
          All Discovered Photos ({avatars.length})
        </h3>
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
          {avatars.map((a, i) => (
            <div
              key={i}
              className={`bg-[#0a0a0f] border rounded-lg p-3 cursor-pointer hover:border-[#00ff88]/30 transition-colors ${
                a.url === primaryAvatar ? 'border-[#00ff88]/40' : 'border-[#1e1e2e]'
              }`}
              onClick={() => setEnlarged(a.url)}
            >
              <img
                src={a.url}
                alt=""
                className="w-full h-32 object-cover rounded"
                onError={(e) => {
                  e.target.parentElement.style.display = 'none'
                }}
              />
              <div className="mt-2 flex items-center justify-between">
                <span className="text-[10px] font-mono text-[#3388ff]">
                  {(a.source || 'unknown').replace(/_profile|_scraper|_search/g, '')}
                </span>
                <div className="flex items-center gap-1">
                  <span className={`text-[9px] px-1.5 py-0.5 rounded font-mono ${
                    getAvatarQuality(a.url) >= 3 ? 'bg-[#00ff88]/15 text-[#00ff88]' :
                    getAvatarQuality(a.url) >= 2 ? 'bg-[#ffcc00]/15 text-[#ffcc00]' :
                    'bg-[#ff2244]/15 text-[#ff2244]'
                  }`}>
                    {getAvatarQuality(a.url) >= 3 ? 'Verified' :
                     getAvatarQuality(a.url) >= 2 ? 'Likely' : 'Default'}
                  </span>
                  {a.url === primaryAvatar && (
                    <span className="text-[9px] bg-[#00ff88]/15 text-[#00ff88] px-1.5 py-0.5 rounded font-mono">
                      Primary
                    </span>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Cross-platform note */}
      {avatars.length >= 2 && (
        <div className="bg-[#12121a] border border-[#1e1e2e] rounded-lg p-4">
          <p className="text-xs text-gray-400">
            {avatars.length} photos discovered across {new Set(avatars.map(a => a.source)).size} sources.
            Cross-platform photo matching can help verify identity consistency.
          </p>
        </div>
      )}

      {/* Enlarged overlay */}
      {enlarged && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/80"
          onClick={() => setEnlarged(null)}
        >
          <div className="relative max-w-lg max-h-[80vh]">
            <img src={enlarged} alt="" className="max-w-full max-h-[80vh] rounded-lg" />
            <button
              onClick={() => setEnlarged(null)}
              className="absolute -top-3 -right-3 bg-[#1e1e2e] rounded-full p-1.5 text-gray-400 hover:text-white"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
