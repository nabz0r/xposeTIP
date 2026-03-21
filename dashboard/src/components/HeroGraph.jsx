/**
 * HeroGraph — animated identity graph for landing page hero.
 *
 * 18 nodes connected by edges. Nodes pulse, edges flow with dashed animation.
 * Center node is the "email" anchor. Surrounding nodes represent
 * findings from different categories (social, breach, metadata).
 *
 * Pure CSS animation, no JS timers. Deterministic layout.
 */

const NODES = [
    // Center — email anchor
    { id: 'email', x: 50, y: 50, r: 8, color: '#00ff88', label: 'you@email', ring: 0 },
    // Ring 1 — social (green)
    { id: 'github', x: 30, y: 30, r: 5, color: '#00ff88', label: 'GitHub' },
    { id: 'reddit', x: 70, y: 28, r: 4.5, color: '#00ff88', label: 'Reddit' },
    { id: 'steam', x: 22, y: 55, r: 4, color: '#00ff88', label: 'Steam' },
    { id: 'twitter', x: 78, y: 52, r: 5, color: '#00ff88', label: 'Twitter' },
    { id: 'linkedin', x: 38, y: 72, r: 4.5, color: '#00ff88', label: 'LinkedIn' },
    { id: 'discord', x: 65, y: 73, r: 4, color: '#00ff88', label: 'Discord' },
    // Ring 2 — metadata/identity (blue)
    { id: 'gravatar', x: 15, y: 38, r: 3.5, color: '#3388ff', label: 'Gravatar' },
    { id: 'dns', x: 85, y: 40, r: 3.5, color: '#3388ff', label: 'DNS' },
    { id: 'geoip', x: 50, y: 18, r: 3, color: '#3388ff', label: 'GeoIP' },
    { id: 'whois', x: 12, y: 68, r: 3, color: '#3388ff', label: 'WHOIS' },
    { id: 'emailrep', x: 88, y: 65, r: 3.5, color: '#3388ff', label: 'EmailRep' },
    // Ring 3 — breach/archive (red/yellow)
    { id: 'breach1', x: 35, y: 12, r: 4, color: '#ff2244', label: 'Breach #1' },
    { id: 'breach2', x: 68, y: 10, r: 3.5, color: '#ff2244', label: 'Breach #2' },
    { id: 'breach3', x: 90, y: 22, r: 3, color: '#ff2244', label: 'Breach #3' },
    { id: 'wayback', x: 10, y: 82, r: 3, color: '#ffcc00', label: 'Wayback' },
    { id: 'paste', x: 50, y: 88, r: 3, color: '#ffcc00', label: 'Pastes' },
    { id: 'tracker', x: 82, y: 82, r: 3, color: '#ffcc00', label: 'Tracker' },
]

const EDGES = [
    // Center to ring 1
    ['email', 'github'], ['email', 'reddit'], ['email', 'steam'],
    ['email', 'twitter'], ['email', 'linkedin'], ['email', 'discord'],
    // Center to ring 2
    ['email', 'gravatar'], ['email', 'dns'], ['email', 'geoip'],
    ['email', 'whois'], ['email', 'emailrep'],
    // Center to ring 3
    ['email', 'breach1'], ['email', 'breach2'], ['email', 'paste'],
    // Cross-connections (same persona)
    ['github', 'reddit'], ['steam', 'discord'],
    ['breach1', 'breach2'], ['breach2', 'breach3'],
    ['linkedin', 'emailrep'], ['gravatar', 'github'],
    ['wayback', 'whois'], ['tracker', 'paste'],
]

export default function HeroGraph({ size = 400, className = '' }) {
    const nodeMap = {}
    NODES.forEach(n => { nodeMap[n.id] = n })

    return (
        <div className={`relative ${className}`} style={{ width: size, height: size }}>
            <svg
                viewBox="0 0 100 100"
                width={size}
                height={size}
                className="hero-graph"
            >
                <defs>
                    {/* Glow filter */}
                    <filter id="glow">
                        <feGaussianBlur stdDeviation="0.8" result="blur" />
                        <feMerge>
                            <feMergeNode in="blur" />
                            <feMergeNode in="SourceGraphic" />
                        </feMerge>
                    </filter>
                    <filter id="glow-strong">
                        <feGaussianBlur stdDeviation="1.5" result="blur" />
                        <feMerge>
                            <feMergeNode in="blur" />
                            <feMergeNode in="SourceGraphic" />
                        </feMerge>
                    </filter>
                </defs>

                {/* Edges */}
                {EDGES.map(([from, to], i) => {
                    const a = nodeMap[from]
                    const b = nodeMap[to]
                    if (!a || !b) return null
                    return (
                        <line
                            key={`e-${i}`}
                            x1={a.x} y1={a.y}
                            x2={b.x} y2={b.y}
                            stroke={a.id === 'email' ? b.color : a.color}
                            strokeWidth="0.3"
                            opacity="0.3"
                            strokeDasharray="1.5 1"
                            className="hero-edge"
                            style={{ animationDelay: `${i * 0.3}s` }}
                        />
                    )
                })}

                {/* Nodes */}
                {NODES.map((node, i) => (
                    <g key={node.id} className="hero-node" style={{ animationDelay: `${i * 0.15}s` }}>
                        {/* Outer glow ring */}
                        <circle
                            cx={node.x} cy={node.y}
                            r={node.r * 1.6}
                            fill="none"
                            stroke={node.color}
                            strokeWidth="0.15"
                            opacity="0.15"
                            className="hero-pulse"
                            style={{ animationDelay: `${i * 0.4}s` }}
                        />
                        {/* Node circle */}
                        <circle
                            cx={node.x} cy={node.y}
                            r={node.r * 0.7}
                            fill={`${node.color}15`}
                            stroke={node.color}
                            strokeWidth={node.id === 'email' ? '0.6' : '0.35'}
                            filter={node.id === 'email' ? 'url(#glow-strong)' : 'url(#glow)'}
                            className="hero-node-circle"
                        />
                        {/* Inner dot */}
                        <circle
                            cx={node.x} cy={node.y}
                            r={node.r * 0.2}
                            fill={node.color}
                            opacity="0.8"
                        />
                        {/* Label */}
                        <text
                            x={node.x}
                            y={node.y + node.r + 2.5}
                            fill="#666"
                            fontSize="1.8"
                            fontFamily="'JetBrains Mono', monospace"
                            textAnchor="middle"
                        >
                            {node.label}
                        </text>
                    </g>
                ))}
            </svg>

            {/* CSS animations */}
            <style>{`
                .hero-graph {
                    animation: hero-rotate 120s linear infinite;
                }
                @keyframes hero-rotate {
                    from { transform: rotate(0deg); }
                    to { transform: rotate(360deg); }
                }
                .hero-edge {
                    animation: edge-flow 3s linear infinite;
                }
                @keyframes edge-flow {
                    from { stroke-dashoffset: 0; }
                    to { stroke-dashoffset: -5; }
                }
                .hero-pulse {
                    animation: node-pulse 3s ease-in-out infinite;
                }
                @keyframes node-pulse {
                    0%, 100% { r: inherit; opacity: 0.1; }
                    50% { opacity: 0.3; }
                }
                .hero-node {
                    animation: node-fade-in 0.8s ease-out both;
                }
                @keyframes node-fade-in {
                    from { opacity: 0; transform: scale(0.5); }
                    to { opacity: 1; transform: scale(1); }
                }
                .hero-node-circle:hover {
                    filter: url(#glow-strong);
                    stroke-width: 0.8;
                }
                /* Counter-rotate labels so they stay readable */
                .hero-graph text {
                    animation: hero-counter-rotate 120s linear infinite;
                }
                @keyframes hero-counter-rotate {
                    from { transform: rotate(0deg); }
                    to { transform: rotate(-360deg); }
                }
            `}</style>
        </div>
    )
}
