import Section from '../shared/Section'

export default function TechStack() {
  return (
    <Section className="py-12">
      <div className="max-w-3xl mx-auto px-6 text-center">
        <div className="flex flex-wrap justify-center gap-3">
          {['FastAPI', 'Celery', 'PostgreSQL', 'Redis', 'React', 'D3.js', 'Docker'].map(t => (
            <span key={t} className="text-[11px] font-mono text-gray-500 bg-[#12121a] border border-[#1e1e2e] rounded-full px-3 py-1">
              {t}
            </span>
          ))}
        </div>
      </div>
    </Section>
  )
}
