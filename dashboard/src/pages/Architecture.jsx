import Section from '../components/shared/Section'
import Stages from '../components/architecture/Stages'
import ScraperBreakdown from '../components/architecture/ScraperBreakdown'
import HeroDiagram from '../components/architecture/HeroDiagram'
import BFPLayer from '../components/architecture/BFPLayer'
import DesignPrinciples from '../components/architecture/DesignPrinciples'
import RoadmapSection from '../components/architecture/RoadmapSection'
import ArchCTA from '../components/architecture/ArchCTA'
import TechStackSection from '../components/architecture/TechStackSection'
import PublicNav from '../components/landing/PublicNav'
import PublicFooter from '../components/landing/PublicFooter'

export default function Architecture() {
  const demoSeed = {
    num_points: 7, rotation: 142, inner_radius: 0.48,
    hue: 158, saturation: 65, lightness: 52,
    eigenvalues: [1.2, 0.8, 0.5, 0.3, 0.1], complexity: 4, email_hash: 4217,
  }

  return (
    <div className="min-h-screen bg-[#0a0a0f] text-white">
      <PublicNav />

      <div className="pt-24 pb-20">
        {/* Hero */}
        <Section className="py-20">
          <div className="max-w-5xl mx-auto px-6">
            <div className="text-center max-w-3xl mx-auto">
              <h1 className="text-4xl md:text-5xl font-bold mb-4 font-['Instrument_Sans',sans-serif]">
                How <span className="text-[#00ff88]">xposeTIP</span> builds identities
              </h1>
              <p className="text-lg text-gray-400 max-w-xl mx-auto mb-4">
                From a single email to a multi-dimensional identity portrait.
                Discover, enrich, identify — a three-phase pipeline that turns noise into signal.
              </p>
            </div>

            {/* NEW S207: animated system diagram */}
            <HeroDiagram />

            <div className="flex flex-wrap items-center justify-center gap-x-8 gap-y-3 pt-8 border-t border-[#1e1e2e] mt-4">
              <div className="flex items-baseline gap-1.5">
                <span className="text-[#00ff88] font-mono font-bold text-xl">174</span>
                <span className="text-xs text-gray-500 font-mono">sources</span>
              </div>
              <span className="text-gray-700">·</span>
              <div className="flex items-baseline gap-1.5">
                <span className="text-[#00ff88] font-mono font-bold text-xl">11</span>
                <span className="text-xs text-gray-500 font-mono">axes</span>
              </div>
              <span className="text-gray-700">·</span>
              <div className="flex items-baseline gap-1.5">
                <span className="text-[#00ff88] font-mono font-bold text-xl">5.4B</span>
                <span className="text-xs text-gray-500 font-mono">avatars</span>
              </div>
              <span className="text-gray-700">·</span>
              <div className="flex items-baseline gap-1.5">
                <span className="text-[#00ff88] font-mono font-bold text-xl">11</span>
                <span className="text-xs text-gray-500 font-mono">stages</span>
              </div>
              <span className="text-gray-700">·</span>
              <div className="flex items-baseline gap-1.5">
                <span className="text-[#00ff88] font-mono font-bold text-xl">0</span>
                <span className="text-xs text-gray-500 font-mono">GPU</span>
              </div>
            </div>
          </div>
        </Section>

        <Stages demoSeed={demoSeed} />

        <BFPLayer />

        <ScraperBreakdown />
        <DesignPrinciples />
        <TechStackSection />

        {/* PDF Report */}
        <Section className="py-12">
          <div className="max-w-3xl mx-auto px-6 text-center">
            <p className="text-gray-500 text-sm">
              Every scan produces a <span className="text-white font-semibold">5-page PDF identity report</span> —
              dark-themed, plan-tiered, downloadable. Built with ReportLab.
            </p>
          </div>
        </Section>

        <RoadmapSection />
        <ArchCTA />
      </div>

      <PublicFooter />
    </div>
  )
}
