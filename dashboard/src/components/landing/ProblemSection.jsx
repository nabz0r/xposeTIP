import Section from '../shared/Section'
import LiveCounter from './LiveCounter'

export default function ProblemSection() {
  return (
    <Section className="py-32">
      <div className="max-w-3xl mx-auto px-6 text-center">
        <LiveCounter />
        <p className="text-lg md:text-xl text-gray-300 leading-relaxed max-w-xl mx-auto mt-8">
          Your email is probably in there. An attacker can find your name, your accounts,
          your habits — in 30 seconds.
        </p>
        <p className="text-lg md:text-xl text-gray-300 leading-relaxed mt-6 max-w-xl mx-auto">
          We know because <span className="text-white font-semibold">we do the same thing</span>.
          <br />
          The difference? We show you how to fix it.
        </p>
      </div>
    </Section>
  )
}
