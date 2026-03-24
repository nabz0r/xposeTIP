import { Link } from 'react-router-dom'
import { Shield, ArrowLeft } from 'lucide-react'
import Section from '../components/shared/Section'
import { StageCollect, StageGraph, StagePropagate, StageScore, StageIdentify, StageExpose, StageMeasure, StageLocate } from '../components/architecture/Stages'
import ScraperBreakdown from '../components/architecture/ScraperBreakdown'
import DesignPrinciples from '../components/architecture/DesignPrinciples'
import RoadmapSection from '../components/architecture/RoadmapSection'
import { ArchCTA, ArchFooter } from '../components/architecture/ArchFooter'

export default function Architecture() {
  const demoSeed = {
    num_points: 7, rotation: 142, inner_radius: 0.48,
    hue: 158, saturation: 65, lightness: 52,
    eigenvalues: [1.2, 0.8, 0.5, 0.3, 0.1], complexity: 4, email_hash: 4217,
  }

  return (
    <div className="min-h-screen bg-[#0a0a0f] text-white">
      {/* Nav */}
      <nav className="fixed top-0 left-0 right-0 z-50 bg-[#0a0a0f]/90 backdrop-blur border-b border-[#1e1e2e]">
        <div className="max-w-5xl mx-auto px-6 py-4 flex items-center justify-between">
          <Link to="/welcome" className="flex items-center gap-2 text-gray-400 hover:text-white transition-colors">
            <ArrowLeft className="w-4 h-4" />
            <Shield className="w-5 h-5 text-[#00ff88]" />
            <span className="font-bold font-['Instrument_Sans',sans-serif]">xpose</span>
          </Link>
          <span className="text-xs text-gray-600 font-mono">Architecture</span>
        </div>
      </nav>

      <div className="pt-24 pb-20">
        {/* Hero */}
        <Section className="py-20">
          <div className="max-w-3xl mx-auto px-6 text-center">
            <h1 className="text-4xl md:text-5xl font-bold mb-4 font-['Instrument_Sans',sans-serif]">
              Architecture — How <span className="text-[#00ff88]">xpose</span> Works
            </h1>
            <p className="text-lg text-gray-400 max-w-xl mx-auto">
              A deep dive into the two-pass intelligence pipeline.
              117 sources, 9-axis radar, one identity graph.
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
        <RoadmapSection />
        <ArchCTA />
      </div>

      <ArchFooter />
    </div>
  )
}
