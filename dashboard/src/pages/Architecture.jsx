import Section from '../components/shared/Section'
import { StageCollect, StageGraph, StagePropagate, StageScore, StageIdentify, StageExpose, StageMeasure, StageLocate } from '../components/architecture/Stages'
import ScraperBreakdown from '../components/architecture/ScraperBreakdown'
import DesignPrinciples from '../components/architecture/DesignPrinciples'
import RoadmapSection from '../components/architecture/RoadmapSection'
import ArchCTA from '../components/architecture/ArchCTA'
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
          <div className="max-w-3xl mx-auto px-6 text-center">
            <h1 className="text-4xl md:text-5xl font-bold mb-4 font-['Instrument_Sans',sans-serif]">
              How <span className="text-[#00ff88]">xposeTIP</span> builds identities
            </h1>
            <p className="text-lg text-gray-400 max-w-xl mx-auto">
              From a single email to a multi-dimensional identity portrait.
              Discover, enrich, identify — the three-stage pipeline that turns noise into signal.
            </p>
          </div>
        </Section>

        <StageCollect />
        <StageGraph />
        <StagePropagate />
        <StageScore />
        <StageIdentify demoSeed={demoSeed} />
        <StageExpose />
        <StageMeasure />
        <ScraperBreakdown />
        <DesignPrinciples />
        <StageLocate />

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
