/**
 * GenerativeAvatar — deterministic SVG avatar from fingerprint data.
 *
 * Generates a unique abstract shape per identity based on:
 * - Graph eigenvalues -> shape complexity
 * - Axes values -> color palette
 * - Email hash -> base rotation and form
 *
 * Same data = same avatar. Data changes = avatar evolves.
 */
export default function GenerativeAvatar({ seed, size = 40, className = '' }) {
    if (!seed) return null

    const { num_points, rotation, inner_radius, hue, saturation, lightness, complexity, email_hash } = seed
    const cx = size / 2
    const cy = size / 2
    const outerR = size * 0.42
    const innerR = outerR * inner_radius

    // Generate star/polygon points
    const points = []
    for (let i = 0; i < num_points * 2; i++) {
        const angle = (Math.PI * 2 * i) / (num_points * 2) + (rotation * Math.PI / 180)
        const r = i % 2 === 0 ? outerR : innerR
        // Add slight irregularity from email_hash
        const jitter = 1 + ((email_hash * (i + 1) * 7) % 20 - 10) / 100
        points.push({
            x: cx + r * jitter * Math.cos(angle),
            y: cy + r * jitter * Math.sin(angle),
        })
    }

    const pathD = points.map((p, i) => `${i === 0 ? 'M' : 'L'} ${p.x.toFixed(1)} ${p.y.toFixed(1)}`).join(' ') + ' Z'

    // Colors
    const mainColor = `hsl(${hue}, ${saturation}%, ${lightness}%)`
    const glowColor = `hsla(${hue}, ${saturation}%, ${lightness}%, 0.3)`
    const bgColor = `hsla(${hue}, ${saturation}%, ${lightness}%, 0.08)`

    // Orbital rings from eigenvalues
    const rings = (seed.eigenvalues || []).slice(0, 3).map((ev, i) => ({
        r: outerR * (0.6 + ev * 0.4),
        opacity: 0.1 + ev * 0.15,
        dasharray: `${ev * 10} ${(1 - ev) * 8}`,
    }))

    return (
        <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} className={className}>
            {/* Background glow */}
            <circle cx={cx} cy={cy} r={outerR * 1.1} fill={bgColor} />

            {/* Orbital rings (from eigenvalues) */}
            {rings.map((ring, i) => (
                <circle key={i} cx={cx} cy={cy} r={ring.r} fill="none"
                    stroke={mainColor} strokeWidth="0.5" opacity={ring.opacity}
                    strokeDasharray={ring.dasharray} />
            ))}

            {/* Main shape */}
            <path d={pathD} fill={glowColor} stroke={mainColor} strokeWidth="1.5" />

            {/* Center dot */}
            <circle cx={cx} cy={cy} r={size * 0.04} fill={mainColor} />

            {/* Complexity indicator dots */}
            {Array.from({ length: Math.min(complexity, 5) }).map((_, i) => {
                const dotAngle = (Math.PI * 2 * i / Math.min(complexity, 5)) + rotation * Math.PI / 180
                const dotR = outerR * 0.3
                return (
                    <circle key={`dot-${i}`}
                        cx={cx + dotR * Math.cos(dotAngle)}
                        cy={cy + dotR * Math.sin(dotAngle)}
                        r={size * 0.02} fill={mainColor} opacity="0.6" />
                )
            })}
        </svg>
    )
}
