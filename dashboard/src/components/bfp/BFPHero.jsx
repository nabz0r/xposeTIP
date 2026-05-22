import BFPInversionVisual from './BFPInversionVisual'

export default function BFPHero() {
  return (
    <section className="py-20">
      <div className="max-w-3xl mx-auto px-6 text-center">
        <div className="inline-flex items-center gap-2 text-xs font-mono text-[#00ff88]/70 mb-6">
          <span className="w-1.5 h-1.5 bg-[#00ff88] rounded-full animate-pulse" />
          Behavioral Fingerprint Protocol · Draft v0
        </div>

        <BFPInversionVisual />

        <h1 className="text-4xl md:text-5xl lg:text-6xl font-bold tracking-tight leading-[1.1] mb-8 font-['Instrument_Sans',sans-serif]">
          The internet knows who you are.<br />
          The world knows who you are.<br />
          <span className="text-[#00ff88] italic">Except you.</span>
        </h1>

        <p className="text-lg md:text-xl text-gray-400 max-w-2xl mx-auto mb-12 leading-relaxed">
          <span className="text-white font-medium">BFP</span> is the layer that returns this knowledge to its subject.
          Information asymmetry becomes symmetry — no new surveillance, vision restored.
        </p>

        <div className="flex flex-wrap items-center justify-center gap-x-8 gap-y-3 pt-8 border-t border-[#1e1e2e]">
          <div className="flex items-baseline gap-1.5">
            <span className="text-[#00ff88] font-mono font-bold text-base">Protocol</span>
            <span className="text-xs text-gray-500 font-mono">not product</span>
          </div>
          <span className="text-gray-700">·</span>
          <div className="flex items-baseline gap-1.5">
            <span className="text-[#00ff88] font-mono font-bold text-base">Subject</span>
            <span className="text-xs text-gray-500 font-mono">sovereignty</span>
          </div>
          <span className="text-gray-700">·</span>
          <div className="flex items-baseline gap-1.5">
            <span className="text-[#00ff88] font-mono font-bold text-base">Post-quantum</span>
            <span className="text-xs text-gray-500 font-mono">NIST 2024</span>
          </div>
          <span className="text-gray-700">·</span>
          <div className="flex items-baseline gap-1.5">
            <span className="text-[#00ff88] font-mono font-bold text-base">Local-first</span>
            <span className="text-xs text-gray-500 font-mono">no cloud lock-in</span>
          </div>
        </div>
      </div>
    </section>
  )
}
