export default function BFPInversionVisual() {
  return (
    <div className="flex justify-center mb-8" aria-label="The Inversion — asymmetric extraction with symmetric vision restored through BFP">
      <svg width="280" height="220" viewBox="0 0 280 220" role="img" className="opacity-90">
        <title>The Inversion</title>
        <desc>Subject at center surrounded by extraction sources; BFP ring restores symmetric vision outward to those same sources.</desc>
        <defs>
          <marker id="bfp-arr" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="5" markerHeight="5" orient="auto-start-reverse">
            <path d="M2 1L8 5L2 9" fill="none" stroke="context-stroke" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
          </marker>
        </defs>

        {/* 6 actor circles */}
        <circle cx="220" cy="110" r="5" fill="#888" opacity="0.45"/>
        <circle cx="180" cy="179" r="5" fill="#888" opacity="0.45"/>
        <circle cx="100" cy="179" r="5" fill="#888" opacity="0.45"/>
        <circle cx="60" cy="110" r="5" fill="#888" opacity="0.45"/>
        <circle cx="100" cy="41" r="5" fill="#888" opacity="0.45"/>
        <circle cx="180" cy="41" r="5" fill="#888" opacity="0.45"/>

        {/* 6 inward extraction arrows — dashed gray, ambient */}
        <line x1="215" y1="110" x2="168" y2="110" stroke="#888" strokeWidth="0.8" strokeOpacity="0.25" strokeDasharray="3,3"/>
        <line x1="178" y1="175" x2="154" y2="134" stroke="#888" strokeWidth="0.8" strokeOpacity="0.25" strokeDasharray="3,3"/>
        <line x1="102" y1="175" x2="126" y2="134" stroke="#888" strokeWidth="0.8" strokeOpacity="0.25" strokeDasharray="3,3"/>
        <line x1="65" y1="110" x2="112" y2="110" stroke="#888" strokeWidth="0.8" strokeOpacity="0.25" strokeDasharray="3,3"/>
        <line x1="102" y1="45" x2="126" y2="86" stroke="#888" strokeWidth="0.8" strokeOpacity="0.25" strokeDasharray="3,3"/>
        <line x1="178" y1="45" x2="154" y2="86" stroke="#888" strokeWidth="0.8" strokeOpacity="0.25" strokeDasharray="3,3"/>

        {/* BFP ring */}
        <circle cx="140" cy="110" r="28" fill="none" stroke="#00ff88" strokeWidth="1.5" opacity="0.85"/>

        {/* Subject 4x4 hash grid centered at (140, 110), cells 4x4 with 1px gap, origin (131, 101) */}
        <g transform="translate(131, 101)">
          <rect x="0" y="0" width="4" height="4" fill="#00ff88" opacity="0.55"/>
          <rect x="5" y="0" width="4" height="4" fill="#00ff88" opacity="0.9"/>
          <rect x="10" y="0" width="4" height="4" fill="#00ff88" opacity="0.65"/>
          <rect x="15" y="0" width="4" height="4" fill="#00ff88" opacity="0.5"/>
          <rect x="0" y="5" width="4" height="4" fill="#00ff88" opacity="0.75"/>
          <rect x="5" y="5" width="4" height="4" fill="#00ff88" opacity="0.55"/>
          <rect x="10" y="5" width="4" height="4" fill="#00ff88" opacity="0.9"/>
          <rect x="15" y="5" width="4" height="4" fill="#00ff88" opacity="0.65"/>
          <rect x="0" y="10" width="4" height="4" fill="#00ff88" opacity="0.65"/>
          <rect x="5" y="10" width="4" height="4" fill="#00ff88" opacity="0.9"/>
          <rect x="10" y="10" width="4" height="4" fill="#00ff88" opacity="0.5"/>
          <rect x="15" y="10" width="4" height="4" fill="#00ff88" opacity="0.75"/>
          <rect x="0" y="15" width="4" height="4" fill="#00ff88" opacity="0.5"/>
          <rect x="5" y="15" width="4" height="4" fill="#00ff88" opacity="0.65"/>
          <rect x="10" y="15" width="4" height="4" fill="#00ff88" opacity="0.9"/>
          <rect x="15" y="15" width="4" height="4" fill="#00ff88" opacity="0.5"/>
        </g>

        {/* 6 outward vision arrows — teal, prominent */}
        <line x1="168" y1="110" x2="213" y2="110" stroke="#00ff88" strokeWidth="1.5" opacity="0.85" markerEnd="url(#bfp-arr)"/>
        <line x1="154" y1="134" x2="177" y2="173" stroke="#00ff88" strokeWidth="1.5" opacity="0.85" markerEnd="url(#bfp-arr)"/>
        <line x1="126" y1="134" x2="104" y2="173" stroke="#00ff88" strokeWidth="1.5" opacity="0.85" markerEnd="url(#bfp-arr)"/>
        <line x1="112" y1="110" x2="67" y2="110" stroke="#00ff88" strokeWidth="1.5" opacity="0.85" markerEnd="url(#bfp-arr)"/>
        <line x1="126" y1="86" x2="104" y2="47" stroke="#00ff88" strokeWidth="1.5" opacity="0.85" markerEnd="url(#bfp-arr)"/>
        <line x1="154" y1="86" x2="177" y2="47" stroke="#00ff88" strokeWidth="1.5" opacity="0.85" markerEnd="url(#bfp-arr)"/>
      </svg>
    </div>
  )
}
