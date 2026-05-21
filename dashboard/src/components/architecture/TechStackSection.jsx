import Section from '../shared/Section'

const STACK_GROUPS = [
  {
    group: 'Backend',
    color: '#3388ff',
    items: ['Python 3.11', 'FastAPI', 'SQLAlchemy 2.0', 'Celery', 'Alembic', 'pgvector', 'asyncio'],
  },
  {
    group: 'Storage',
    color: '#aa55ff',
    items: ['PostgreSQL 16', 'Redis 7', 'Fernet (AES-256)', 'JSONB'],
  },
  {
    group: 'Frontend',
    color: '#00ff88',
    items: ['React 18', 'Vite', 'Tailwind CSS 4', 'D3.js', 'Recharts', 'TopoJSON 110m'],
  },
  {
    group: 'Output & Auth',
    color: '#ffcc00',
    items: ['ReportLab (PDF)', 'JWT', 'OAuth 2.0', 'SSE', 'Docker Compose'],
  },
]

export default function TechStackSection() {
  return (
    <Section className="py-20 bg-[#12121a]/50">
      <div className="max-w-4xl mx-auto px-6">
        <h2 className="text-2xl font-bold mb-4 text-center font-['Instrument_Sans',sans-serif]">Tech Stack</h2>
        <p className="text-center text-gray-500 text-sm mb-10 max-w-lg mx-auto">
          One stack. One PostgreSQL. Zero GPU.
          Built to run on a single box without cloud bloat — the Amiga 500 philosophy applied to threat intelligence.
        </p>
        <div className="grid md:grid-cols-2 gap-5">
          {STACK_GROUPS.map(g => (
            <div key={g.group} className="bg-[#0a0a0f] border border-[#1e1e2e] rounded-xl p-5">
              <h3 className="text-sm font-semibold mb-3 font-mono" style={{ color: g.color }}>{g.group}</h3>
              <div className="flex flex-wrap gap-2">
                {g.items.map(t => (
                  <span key={t} className="text-xs font-mono text-gray-400 bg-[#1e1e2e] px-2.5 py-1 rounded">
                    {t}
                  </span>
                ))}
              </div>
            </div>
          ))}
        </div>
        <p className="text-center text-[10px] text-gray-700 font-mono mt-8">
          Open source · AGPL-3.0 · github.com/nabz0r/xposeTIP
        </p>
      </div>
    </Section>
  )
}
