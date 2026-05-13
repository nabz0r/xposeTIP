import { Users, KeyRound, Newspaper, Fingerprint, Share2, ShieldCheck } from 'lucide-react'

export const DEMO_AVATARS = [
  { email_hash: 12345, score: 15 },
  { email_hash: 67890, score: 35 },
  { email_hash: 33333, score: 55 },
  { email_hash: 44444, score: 72 },
  { email_hash: 55555, score: 25 },
  { email_hash: 77777, score: 85 },
  { email_hash: 88888, score: 45 },
  { email_hash: 10101, score: 65 },
  { email_hash: 20202, score: 92 },
]

export const DEFAULT_SEED_PROPS = { hue: 140, num_points: 6, rotation: 45, saturation: 70, lightness: 50, inner_radius: 0.5, complexity: 3 }

export const scoreColor = (score) => {
  if (score >= 80) return '#ff2244'
  if (score >= 60) return '#ff8800'
  if (score >= 40) return '#ffcc00'
  if (score >= 20) return '#3388ff'
  return '#00ff88'
}

export const sevColor = (sev) => {
  if (sev === 'critical') return { bg: 'bg-[#ff2244]/20', text: 'text-[#ff2244]' }
  if (sev === 'high') return { bg: 'bg-[#ff8800]/20', text: 'text-[#ff8800]' }
  if (sev === 'medium') return { bg: 'bg-[#ffcc00]/20', text: 'text-[#ffcc00]' }
  return { bg: 'bg-[#3388ff]/20', text: 'text-[#3388ff]' }
}

export const PHASES = [
  { until: 15, msg: 'Starting scan...' },
  { until: 40, msg: 'Checking breach databases...' },
  { until: 80, msg: 'Scanning social networks...' },
  { until: 120, msg: 'Analyzing DNS & email security...' },
  { until: 180, msg: 'Cross-referencing usernames...' },
  { until: 240, msg: 'Building your identity profile...' },
  { until: 300, msg: 'Finalizing results...' },
]

export const EXPOSURES = [
  { icon: Users, title: 'Digital Footprint Discovery', desc: 'Identify accounts across 35+ social platforms, dev tools, gaming sites. Detect username reuse and cross-platform linkage.' },
  { icon: KeyRound, title: 'Breach & Leak Intelligence', desc: 'Check exposure in data breaches, leaked credentials, and paste sites. Timeline of when data was compromised.' },
  { icon: Newspaper, title: 'Public Exposure Intelligence', desc: 'Automated news monitoring across global media. Sanctions & PEP screening via 40+ watchlists. Corporate directorship tracking.' },
  { icon: Fingerprint, title: '9-Axis Behavioral Radar', desc: 'Unique digital fingerprint across 9 dimensions: accounts, platforms, email age, breaches, username reuse, data leaked, geo spread, security posture, and public exposure.' },
  { icon: Share2, title: 'Identity Graph & Personas', desc: 'PageRank-based confidence propagation. Automatic persona clustering. Name resolution with operator override.' },
  { icon: ShieldCheck, title: 'Compliance Ready', desc: 'Sanctions screening (OFAC, EU, UN, Interpol). PEP detection. Corporate officer identification. Built for KYC/AML workflows.' },
]

export const AUDIENCES = [
  {
    label: 'Free',
    desc: 'Check your own exposure.',
    price: '€0 forever',
    href: '/setup',
    cta: 'Start free',
    features: ['25 quick scans / month', 'Basic exposure check', '9-axis fingerprint preview', 'Single identifier'],
  },
  {
    label: 'Starter',
    desc: 'For individual professionals.',
    price: '€49/month',
    href: '/setup?plan=starter',
    cta: 'Join waitlist',
    features: ['250 full scans / month', 'Full 124-source pipeline', 'Identity graph + personas', 'PDF identity reports'],
  },
  {
    label: 'Team',
    desc: 'For security teams.',
    price: '€299/month',
    href: '/setup?plan=team',
    cta: 'Join waitlist',
    features: ['2 000 scans / month', '5 seats included', 'API access (SIEM/SOAR)', 'Multi-workspace + shared targets'],
  },
  {
    label: 'Enterprise',
    desc: 'For organizations.',
    price: 'From €2 500/month',
    href: 'mailto:contact@redbird.co.com?subject=xposeTIP%20Enterprise%20inquiry',
    cta: 'Contact sales',
    features: ['Multi-tenant + SSO', 'Audit log + SLA', 'Custom scrapers on demand', 'Managed third-party API integrations'],
  },
]

export function hashEmail(email) {
  let hash = 0
  for (let i = 0; i < (email || '').length; i++) {
    hash = ((hash << 5) - hash) + email.charCodeAt(i)
    hash |= 0
  }
  return Math.abs(hash)
}
