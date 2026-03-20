import React from 'react'

const PLATFORMS = {
  spotify: { color: '#1DB954', label: 'Spotify' },
  amazon: { color: '#FF9900', label: 'Amazon' },
  github: { color: '#f0f0f0', label: 'GitHub' },
  reddit: { color: '#FF4500', label: 'Reddit' },
  steam: { color: '#1B2838', label: 'Steam' },
  keybase: { color: '#FF6F21', label: 'Keybase' },
  twitter: { color: '#1DA1F2', label: 'Twitter' },
  x: { color: '#f0f0f0', label: 'X' },
  linkedin: { color: '#0077B5', label: 'LinkedIn' },
  facebook: { color: '#1877F2', label: 'Facebook' },
  instagram: { color: '#E4405F', label: 'Instagram' },
  tiktok: { color: '#f0f0f0', label: 'TikTok' },
  youtube: { color: '#FF0000', label: 'YouTube' },
  pinterest: { color: '#E60023', label: 'Pinterest' },
  tumblr: { color: '#36465D', label: 'Tumblr' },
  discord: { color: '#5865F2', label: 'Discord' },
  gitlab: { color: '#FC6D26', label: 'GitLab' },
  medium: { color: '#00AB6C', label: 'Medium' },
  hackernews: { color: '#FF6600', label: 'HackerNews' },
  devto: { color: '#0A0A0A', label: 'Dev.to' },
  snapchat: { color: '#FFFC00', label: 'Snapchat' },
  telegram: { color: '#26A5E4', label: 'Telegram' },
  whatsapp: { color: '#25D366', label: 'WhatsApp' },
  mastodon: { color: '#6364FF', label: 'Mastodon' },
  twitch: { color: '#9146FF', label: 'Twitch' },
}

const REMEDIATION_LINKS = {
  spotify: 'https://www.spotify.com/account/security/',
  amazon: 'https://www.amazon.com/gp/css/account/info/view.html',
  github: 'https://github.com/settings/security',
  reddit: 'https://www.reddit.com/prefs/update/',
  steam: 'https://store.steampowered.com/account/',
  keybase: 'https://keybase.io/account',
  google: 'https://myaccount.google.com/security',
  facebook: 'https://www.facebook.com/settings?tab=security',
  twitter: 'https://twitter.com/settings/security',
  linkedin: 'https://www.linkedin.com/psettings/sign-in-and-security',
  instagram: 'https://www.instagram.com/accounts/privacy_and_security/',
  tiktok: 'https://www.tiktok.com/setting',
  pinterest: 'https://www.pinterest.com/settings/security/',
  youtube: 'https://myaccount.google.com/security',
  discord: 'https://discord.com/channels/@me',
  gitlab: 'https://gitlab.com/-/profile/account',
  medium: 'https://medium.com/me/settings/security',
  tumblr: 'https://www.tumblr.com/settings/account',
}

export function getPlatformInfo(name) {
  const key = (name || '').toLowerCase().replace(/[^a-z0-9]/g, '')
  return PLATFORMS[key] || null
}

export function getRemediationLink(name) {
  const key = (name || '').toLowerCase().replace(/[^a-z0-9]/g, '')
  return REMEDIATION_LINKS[key] || null
}

export default function PlatformIcon({ platform, size = 'md', showLabel = true, url, username }) {
  const key = (platform || '').toLowerCase().replace(/[^a-z0-9]/g, '')
  const info = PLATFORMS[key]
  const color = info?.color || '#666688'
  const label = info?.label || platform
  const remLink = REMEDIATION_LINKS[key]

  const sizeClasses = {
    sm: 'w-6 h-6 text-[10px]',
    md: 'w-8 h-8 text-xs',
    lg: 'w-10 h-10 text-sm',
  }

  // Use Google favicon service for icons
  const faviconUrl = platform && platform.includes('.')
    ? `https://www.google.com/s2/favicons?domain=${platform}&sz=32`
    : key ? `https://www.google.com/s2/favicons?domain=${key}.com&sz=32` : null

  return (
    <div className="inline-flex items-center gap-2 px-2.5 py-1.5 rounded-lg bg-[#12121a] border border-[#1e1e2e] hover:border-opacity-50 transition-colors group"
         style={{ borderColor: `${color}30` }}>
      <div className={`${sizeClasses[size]} rounded-full flex items-center justify-center overflow-hidden`}
           style={{ backgroundColor: `${color}20` }}>
        {faviconUrl ? (
          <img src={faviconUrl} alt="" className="w-4 h-4" onError={e => { e.target.style.display = 'none' }} />
        ) : (
          <span className="font-bold" style={{ color }}>{(label || '?')[0].toUpperCase()}</span>
        )}
      </div>
      {showLabel && (
        <div className="min-w-0">
          <div className="text-xs font-medium truncate" style={{ color }}>{label}</div>
          {username && <div className="text-[10px] text-gray-500 font-mono truncate">@{username}</div>}
        </div>
      )}
      {url && (
        <a href={url} target="_blank" rel="noreferrer"
           className="text-gray-600 hover:text-[#3388ff] ml-auto"
           onClick={e => e.stopPropagation()}>
          <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
          </svg>
        </a>
      )}
      {remLink && (
        <a href={remLink} target="_blank" rel="noreferrer"
           className="text-[10px] text-gray-600 hover:text-[#00ff88] ml-1 whitespace-nowrap opacity-0 group-hover:opacity-100 transition-opacity"
           onClick={e => e.stopPropagation()}>
          Secure
        </a>
      )}
    </div>
  )
}
