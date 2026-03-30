import Section from '../shared/Section'
import { AtSign, Users, Fingerprint } from 'lucide-react'

export default function FeaturesSection() {
  return (
    <Section className="py-32">
      <div className="max-w-3xl mx-auto px-6">
        <h2 className="text-3xl md:text-4xl font-bold text-center mb-6 font-['Instrument_Sans',sans-serif]">
          The Journey
        </h2>
        <p className="text-center text-gray-500 text-sm mb-16 max-w-lg mx-auto">
          From one email to a complete identity. Not a list of indicators — a person.
        </p>

        <div className="bg-[#12121a] border border-[#1e1e2e] rounded-xl p-8 md:p-10">
          <div className="space-y-6 text-lg text-gray-400 leading-relaxed">
            <p>
              You enter an email.
            </p>
            <p>
              2 minutes later you don't get a list of 500 indicators.
            </p>
            <p className="text-white font-semibold text-xl">
              You get a person.
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-6 mt-10 mb-10">
            <div className="flex flex-col items-center text-center gap-3">
              <div className="w-12 h-12 rounded-xl bg-[#3388ff]/10 flex items-center justify-center">
                <AtSign className="w-6 h-6 text-[#3388ff]" />
              </div>
              <div>
                <div className="text-2xl font-mono font-bold text-white">33</div>
                <div className="text-xs text-gray-500">accounts across the internet</div>
              </div>
            </div>
            <div className="flex flex-col items-center text-center gap-3">
              <div className="w-12 h-12 rounded-xl bg-[#ff2244]/10 flex items-center justify-center">
                <Users className="w-6 h-6 text-[#ff2244]" />
              </div>
              <div>
                <div className="text-2xl font-mono font-bold text-white">3</div>
                <div className="text-xs text-gray-500">data breaches with dates</div>
              </div>
            </div>
            <div className="flex flex-col items-center text-center gap-3">
              <div className="w-12 h-12 rounded-xl bg-[#ff8800]/10 flex items-center justify-center">
                <Fingerprint className="w-6 h-6 text-[#ff8800]" />
              </div>
              <div>
                <div className="text-2xl font-mono font-bold text-white">9</div>
                <div className="text-xs text-gray-500">behavioral dimensions</div>
              </div>
            </div>
          </div>

          <div className="space-y-6 text-lg text-gray-400 leading-relaxed">
            <p>
              4 news articles linking the name to public events.
              A behavioral radar unlike anyone else's.
              And <span className="text-[#00ff88] font-semibold">3 concrete actions</span> to reduce exposure.
            </p>
            <p className="text-gray-500 text-base border-t border-[#1e1e2e] pt-6">
              From noise to signal. From IOC to identity.
            </p>
          </div>
        </div>
      </div>
    </Section>
  )
}
