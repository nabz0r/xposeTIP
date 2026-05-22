import Section from '../components/shared/Section'
import BFPHero from '../components/bfp/BFPHero'
import BFPFoundation from '../components/bfp/BFPFoundation'
import BFPArchitecture from '../components/bfp/BFPArchitecture'
import BFPCryptography from '../components/bfp/BFPCryptography'
import BFPSubjectLayer from '../components/bfp/BFPSubjectLayer'
import BFPEthics from '../components/bfp/BFPEthics'
import BFPStatus from '../components/bfp/BFPStatus'
import BFPRoadmap from '../components/bfp/BFPRoadmap'
import PublicNav from '../components/landing/PublicNav'
import PublicFooter from '../components/landing/PublicFooter'

export default function BFP() {
  return (
    <div className="min-h-screen bg-[#0a0a0f] text-white">
      <PublicNav />
      <div className="pt-24 pb-20">
        <BFPHero />
        <Section className="py-20">
          <BFPFoundation />
        </Section>
        <Section className="py-20 bg-[#0d0d14]">
          <BFPArchitecture />
        </Section>
        <Section className="py-20">
          <BFPCryptography />
        </Section>
        <Section className="py-20 bg-[#0d0d14]">
          <BFPSubjectLayer />
        </Section>
        <Section className="py-20">
          <BFPEthics />
        </Section>
        <Section className="py-20 bg-[#0d0d14]">
          <BFPStatus />
        </Section>
        <Section className="py-20">
          <BFPRoadmap />
        </Section>
      </div>
      <PublicFooter />
    </div>
  )
}
