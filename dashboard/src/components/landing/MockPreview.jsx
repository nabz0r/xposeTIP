import Section from '../shared/Section'
import GenerativeAvatar from '../GenerativeAvatar'
import { DEFAULT_SEED_PROPS } from './constants'

export default function MockPreview() {
  return (
    <Section className="py-32">
      <div className="max-w-3xl mx-auto px-6">
        <h2 className="text-3xl md:text-4xl font-bold text-center mb-4 font-['Instrument_Sans',sans-serif]">
          This is what an identity looks like
        </h2>
        <p className="text-center text-gray-500 text-sm mb-16 max-w-md mx-auto">
          Not a spreadsheet of IOCs. A complete digital persona — scores, accounts, behavioral radar, and remediation.
        </p>

        <div className="bg-[#12121a] border border-[#1e1e2e] rounded-xl p-6 md:p-8 max-w-lg mx-auto">
          <div className="flex items-center gap-4 mb-5">
            <GenerativeAvatar
              seed={{ email_hash: 314159, ...DEFAULT_SEED_PROPS }}
              size={56}
              score={34}
            />
            <div>
              <div className="font-semibold">John Smith</div>
              <div className="text-xs text-gray-500 font-mono">john.smith@gmail.com</div>
            </div>
          </div>

          <div className="flex gap-6 mb-5">
            <div>
              <div className="text-[10px] text-gray-500 uppercase tracking-wider mb-1">Exposure</div>
              <div className="flex items-center gap-2">
                <div className="text-xl font-mono font-bold text-[#ff8800]">34</div>
                <div className="w-24 bg-[#1e1e2e] rounded-full h-1.5">
                  <div className="h-full bg-[#ff8800] rounded-full" style={{ width: '34%' }} />
                </div>
              </div>
            </div>
            <div>
              <div className="text-[10px] text-gray-500 uppercase tracking-wider mb-1">Threat</div>
              <div className="flex items-center gap-2">
                <div className="text-xl font-mono font-bold text-[#3388ff]">22</div>
                <div className="w-24 bg-[#1e1e2e] rounded-full h-1.5">
                  <div className="h-full bg-[#3388ff] rounded-full" style={{ width: '22%' }} />
                </div>
              </div>
            </div>
          </div>

          {/* Persona + location + photos */}
          <div className="flex flex-wrap items-center gap-3 mb-4 text-xs text-gray-400">
            <span className="bg-[#1e1e2e] rounded-full px-2.5 py-1 text-[#3388ff]">@jsmith · Primary persona · 12 platforms</span>
            <span className="bg-[#1e1e2e] rounded-full px-2.5 py-1">{'\ud83d\udccd'} San Francisco, US</span>
            <span className="bg-[#1e1e2e] rounded-full px-2.5 py-1">{'\ud83d\udcf7'} 4 photos</span>
          </div>

          <div className="space-y-2.5 mb-4">
            <div className="flex items-center gap-2 text-sm">
              <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-[#ff2244]/20 text-[#ff2244]">high</span>
              <span className="text-gray-300">Exposed in LinkedIn 2021 breach — email + password hash</span>
            </div>
            <div className="flex items-center gap-2 text-sm">
              <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-[#ffcc00]/20 text-[#ffcc00]">medium</span>
              <span className="text-gray-300">12 accounts discovered across social and dev platforms</span>
            </div>
            <div className="flex items-center gap-2 text-sm">
              <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-[#ffcc00]/20 text-[#ffcc00]">medium</span>
              <span className="text-gray-300">Username "jsmith" reused on 5 platforms — persona linkable</span>
            </div>
            <div className="flex items-center gap-2 text-sm">
              <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-[#3388ff]/20 text-[#3388ff]">info</span>
              <span className="text-gray-300">Behavioral fingerprint: high account spread, moderate security</span>
            </div>
          </div>

          <div className="relative">
            <div className="space-y-2 blur-sm select-none">
              {[1,2,3].map(i => (
                <div key={i} className="flex items-center gap-2 text-sm">
                  <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-gray-800 text-gray-600">low</span>
                  <span className="text-gray-600">Additional identity detail — sign up to view</span>
                </div>
              ))}
            </div>
            <div className="absolute inset-0 flex items-center justify-center">
              <a href="/setup"
                className="bg-[#00ff88] text-black font-bold rounded-lg px-6 py-2.5 text-sm hover:bg-[#00ff88]/90 transition-all hover:scale-105 shadow-lg shadow-[#00ff88]/20">
                See your full identity report — Free
              </a>
            </div>
          </div>
        </div>
      </div>
    </Section>
  )
}
