import Section from '../shared/Section'
import ScanForm from './ScanForm'

export default function FinalCTA({ email, setEmail, loading, error, onSubmit }) {
  return (
    <Section className="py-32">
      <div className="max-w-3xl mx-auto px-6 text-center">
        <h2 className="text-3xl md:text-4xl font-bold mb-6 font-['Instrument_Sans',sans-serif]">
          What does an attacker already know about{' '}
          <span className="text-[#00ff88]">you</span>?
        </h2>

        <div className="flex justify-center mb-4">
          <ScanForm email={email} setEmail={setEmail} loading={loading} error={error} onSubmit={onSubmit} />
        </div>

        <p className="text-sm text-gray-600">
          Free. No credit card. Results in 30 seconds.
        </p>
      </div>
    </Section>
  )
}
