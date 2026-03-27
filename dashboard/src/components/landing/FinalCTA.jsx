import Section from '../shared/Section'
import ScanForm from './ScanForm'

export default function FinalCTA({ email, setEmail, loading, error, onSubmit }) {
  return (
    <Section className="py-32">
      <div className="max-w-3xl mx-auto px-6 text-center">
        <h2 className="text-3xl md:text-4xl font-bold mb-4 font-['Instrument_Sans',sans-serif]">
          Your digital identity is already out there.
        </h2>
        <p className="text-lg text-gray-400 mb-8">
          The question is: do you know what it looks like?
        </p>

        <div className="flex justify-center mb-4">
          <ScanForm email={email} setEmail={setEmail} loading={loading} error={error} onSubmit={onSubmit} />
        </div>

        <p className="text-sm text-gray-600">
          Free. No credit card. Results in 2 minutes.
        </p>
        <p className="text-xs text-gray-500 mt-3">
          Ethical OSINT &middot; Green intelligence &middot; <a href="/manifesto" className="text-[#00ff88] hover:underline">Read our manifesto</a>
        </p>
      </div>
    </Section>
  )
}
