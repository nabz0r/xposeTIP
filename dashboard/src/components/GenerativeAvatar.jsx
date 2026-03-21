/**
 * GenerativeAvatar — 32x32 pixel art identity face (CryptoPunk-style).
 *
 * Deterministic: same seed = same face. ~5.4 billion unique combinations.
 * Score-reactive: expression, background, and glitch effects change with exposure score.
 *
 * Trait system (14 axes):
 *   face_shape, skin_tone, eye_style, eye_color, hair_style, hair_color,
 *   mouth, nose, eyebrows, facial_hair, accessory, clothing, clothing_color, expression
 */

// --- Seeded PRNG (splitmix32) ---
function splitmix32(seed) {
    let s = seed | 0
    return function () {
        s |= 0
        s = (s + 0x9e3779b9) | 0
        let t = s ^ (s >>> 16)
        t = Math.imul(t, 0x21f0aaad)
        t = t ^ (t >>> 15)
        t = Math.imul(t, 0x735a2d97)
        t = t ^ (t >>> 15)
        return (t >>> 0) / 4294967296
    }
}

function seedFromObj(seed) {
    if (!seed) return 0
    const { email_hash = 0, hue = 0, num_points = 5, rotation = 0 } = seed
    return ((email_hash * 2654435761) ^ (hue * 40503) ^ (num_points * 65537) ^ (rotation * 2246822519)) >>> 0
}

// --- Palettes ---
const SKIN_TONES = ['#FFDBB4', '#E8B88A', '#D09060', '#A0714F', '#70503C', '#3D2B1F', '#F5D6C3', '#C89070']
const EYE_COLORS = ['#2244aa', '#44aa44', '#886633', '#222222', '#6633aa', '#aa4444', '#44aaaa', '#888888']
const HAIR_COLORS = ['#1a1a1a', '#4a3728', '#8B4513', '#DAA520', '#D2691E', '#A52A2A', '#DC143C', '#FF4500', '#C0C0C0', '#F0E68C', '#800080', '#1E90FF']
const CLOTHING_COLORS = ['#1a1a2e', '#16213e', '#0f3460', '#533483', '#e94560', '#00ff88', '#ff8800', '#3388ff', '#ffcc00', '#ff2244', '#444444', '#006644']

// --- Trait selection ---
function selectTraits(rng) {
    const pick = (arr) => arr[Math.floor(rng() * arr.length)]
    return {
        faceShape: Math.floor(rng() * 4),     // 0=round, 1=square, 2=oval, 3=angular
        skin: pick(SKIN_TONES),
        eyeStyle: Math.floor(rng() * 8),
        eyeColor: pick(EYE_COLORS),
        hairStyle: Math.floor(rng() * 12),     // 0=bald, 1-11=styles
        hairColor: pick(HAIR_COLORS),
        mouth: Math.floor(rng() * 6),
        nose: Math.floor(rng() * 4),
        eyebrows: Math.floor(rng() * 5),
        facialHair: Math.floor(rng() * 6),     // 0=none, 1-5=styles
        accessory: Math.floor(rng() * 8),      // 0=none, 1-7=styles
        clothing: Math.floor(rng() * 6),
        clothingColor: pick(CLOTHING_COLORS),
        expression: Math.floor(rng() * 4),     // modified by score
    }
}

// --- Pixel buffer helpers ---
function createGrid() {
    return Array.from({ length: 32 }, () => Array(32).fill(null))
}

function setPixel(grid, x, y, color) {
    if (x >= 0 && x < 32 && y >= 0 && y < 32 && color) grid[y][x] = color
}

function fillRect(grid, x, y, w, h, color) {
    for (let dy = 0; dy < h; dy++)
        for (let dx = 0; dx < w; dx++)
            setPixel(grid, x + dx, y + dy, color)
}

function drawEllipse(grid, cx, cy, rx, ry, color) {
    for (let y = cy - ry; y <= cy + ry; y++)
        for (let x = cx - rx; x <= cx + rx; x++) {
            const dx = (x - cx) / rx, dy = (y - cy) / ry
            if (dx * dx + dy * dy <= 1) setPixel(grid, Math.round(x), Math.round(y), color)
        }
}

// --- Face shape templates ---
function drawFace(grid, shape, skin) {
    switch (shape) {
        case 0: // Round
            drawEllipse(grid, 15, 16, 10, 11, skin)
            break
        case 1: // Square
            fillRect(grid, 6, 6, 20, 22, skin)
            // Soften corners
            setPixel(grid, 6, 6, null); setPixel(grid, 25, 6, null)
            setPixel(grid, 6, 27, null); setPixel(grid, 25, 27, null)
            break
        case 2: // Oval
            drawEllipse(grid, 15, 15, 9, 12, skin)
            break
        case 3: // Angular
            fillRect(grid, 7, 7, 18, 20, skin)
            // Jaw taper
            for (let i = 0; i < 3; i++) {
                setPixel(grid, 7 + i, 25 + i, null)
                setPixel(grid, 24 - i, 25 + i, null)
            }
            break
    }
}

// --- Eyes ---
function drawEyes(grid, style, color, expression) {
    const lx = 11, rx = 19, ey = 14
    const stamps = [
        // 0: normal dot
        () => { setPixel(grid, lx, ey, color); setPixel(grid, rx, ey, color) },
        // 1: wide open (2px)
        () => { fillRect(grid, lx - 1, ey, 2, 2, color); fillRect(grid, rx, ey, 2, 2, color) },
        // 2: narrow
        () => { fillRect(grid, lx - 1, ey, 3, 1, color); fillRect(grid, rx - 1, ey, 3, 1, color) },
        // 3: round with pupil
        () => {
            fillRect(grid, lx - 1, ey - 1, 3, 3, '#ffffff')
            fillRect(grid, rx - 1, ey - 1, 3, 3, '#ffffff')
            setPixel(grid, lx, ey, color); setPixel(grid, rx, ey, color)
        },
        // 4: half-closed
        () => { fillRect(grid, lx - 1, ey, 3, 1, color); fillRect(grid, rx - 1, ey, 3, 1, color) },
        // 5: anime (tall)
        () => {
            fillRect(grid, lx - 1, ey - 1, 3, 4, '#ffffff')
            fillRect(grid, rx - 1, ey - 1, 3, 4, '#ffffff')
            fillRect(grid, lx, ey, 1, 2, color); fillRect(grid, rx, ey, 1, 2, color)
        },
        // 6: wink (left closed, right open)
        () => {
            fillRect(grid, lx - 1, ey, 3, 1, color)
            fillRect(grid, rx - 1, ey - 1, 3, 3, '#ffffff')
            setPixel(grid, rx, ey, color)
        },
        // 7: sunglasses (drawn as accessory, leave basic)
        () => { setPixel(grid, lx, ey, color); setPixel(grid, rx, ey, color) },
    ]

    stamps[style % stamps.length]()

    // Expression modifier
    if (expression === 3) {
        // Angry: eyebrow line lowered → override with single-pixel squint
        setPixel(grid, lx, ey - 1, null); setPixel(grid, rx, ey - 1, null)
    }
}

// --- Eyebrows ---
function drawEyebrows(grid, style, hairColor) {
    const y = 11
    switch (style) {
        case 0: // Thin
            fillRect(grid, 10, y, 3, 1, hairColor); fillRect(grid, 18, y, 3, 1, hairColor)
            break
        case 1: // Thick
            fillRect(grid, 9, y, 4, 2, hairColor); fillRect(grid, 18, y, 4, 2, hairColor)
            break
        case 2: // Arched
            setPixel(grid, 10, y + 1, hairColor); fillRect(grid, 11, y, 2, 1, hairColor)
            setPixel(grid, 19, y + 1, hairColor); fillRect(grid, 18, y, 2, 1, hairColor)
            break
        case 3: // Angry
            setPixel(grid, 10, y, hairColor); setPixel(grid, 11, y + 1, hairColor); setPixel(grid, 12, y + 1, hairColor)
            setPixel(grid, 21, y, hairColor); setPixel(grid, 20, y + 1, hairColor); setPixel(grid, 19, y + 1, hairColor)
            break
        case 4: // None
            break
    }
}

// --- Nose ---
function drawNose(grid, style, skin) {
    const darker = darken(skin, 0.85)
    switch (style) {
        case 0: setPixel(grid, 15, 17, darker); break
        case 1: fillRect(grid, 15, 16, 1, 2, darker); break
        case 2: fillRect(grid, 14, 17, 3, 1, darker); break
        case 3: setPixel(grid, 15, 17, darker); setPixel(grid, 14, 18, darker); setPixel(grid, 16, 18, darker); break
    }
}

// --- Mouth ---
function drawMouth(grid, style, expression) {
    const my = 21
    const mouthColor = '#cc3344'
    switch (expression === 3 ? 5 : style) {
        case 0: // Smile
            fillRect(grid, 13, my, 5, 1, mouthColor)
            setPixel(grid, 12, my - 1, mouthColor); setPixel(grid, 18, my - 1, mouthColor)
            break
        case 1: // Neutral
            fillRect(grid, 13, my, 5, 1, mouthColor)
            break
        case 2: // Open
            fillRect(grid, 13, my, 5, 2, mouthColor)
            fillRect(grid, 14, my, 3, 1, '#440000')
            break
        case 3: // Smirk
            fillRect(grid, 14, my, 3, 1, mouthColor)
            setPixel(grid, 17, my - 1, mouthColor)
            break
        case 4: // Grin
            fillRect(grid, 12, my, 7, 1, mouthColor)
            fillRect(grid, 13, my, 5, 1, '#ffffff')
            break
        case 5: // Frown
            fillRect(grid, 13, my, 5, 1, mouthColor)
            setPixel(grid, 12, my + 1, mouthColor); setPixel(grid, 18, my + 1, mouthColor)
            break
    }
}

// --- Facial hair ---
function drawFacialHair(grid, style, color) {
    switch (style) {
        case 0: break // none
        case 1: // Stubble
            for (let x = 10; x < 22; x += 2) setPixel(grid, x, 23, color)
            break
        case 2: // Mustache
            fillRect(grid, 12, 19, 2, 1, color); fillRect(grid, 17, 19, 2, 1, color)
            fillRect(grid, 14, 20, 3, 1, color)
            break
        case 3: // Beard
            fillRect(grid, 10, 22, 11, 3, color)
            fillRect(grid, 11, 25, 9, 1, color)
            fillRect(grid, 12, 26, 7, 1, color)
            break
        case 4: // Goatee
            fillRect(grid, 14, 22, 3, 3, color)
            break
        case 5: // Full (mustache + beard)
            fillRect(grid, 12, 19, 2, 1, color); fillRect(grid, 17, 19, 2, 1, color)
            fillRect(grid, 14, 20, 3, 1, color)
            fillRect(grid, 10, 22, 11, 4, color)
            fillRect(grid, 12, 26, 7, 1, color)
            break
    }
}

// --- Hair ---
function drawHair(grid, style, color) {
    switch (style) {
        case 0: break // bald
        case 1: // Short crop
            fillRect(grid, 7, 4, 18, 4, color)
            fillRect(grid, 6, 6, 2, 8, color); fillRect(grid, 24, 6, 2, 8, color)
            break
        case 2: // Spiky
            fillRect(grid, 8, 5, 16, 3, color)
            for (let i = 0; i < 5; i++) fillRect(grid, 9 + i * 3, 2, 2, 3, color)
            break
        case 3: // Long
            fillRect(grid, 7, 4, 18, 4, color)
            fillRect(grid, 5, 6, 3, 18, color); fillRect(grid, 24, 6, 3, 18, color)
            break
        case 4: // Mohawk
            fillRect(grid, 14, 1, 3, 6, color)
            break
        case 5: // Side part
            fillRect(grid, 7, 4, 18, 4, color)
            fillRect(grid, 5, 5, 3, 12, color)
            break
        case 6: // Buzz
            fillRect(grid, 7, 5, 18, 3, color)
            break
        case 7: // Afro
            drawEllipse(grid, 15, 7, 12, 8, color)
            break
        case 8: // Bangs
            fillRect(grid, 7, 4, 18, 4, color)
            fillRect(grid, 8, 8, 10, 3, color)
            break
        case 9: // Ponytail
            fillRect(grid, 7, 4, 18, 4, color)
            fillRect(grid, 24, 4, 3, 3, color)
            fillRect(grid, 26, 7, 2, 8, color)
            break
        case 10: // Undercut
            fillRect(grid, 9, 4, 14, 4, color)
            fillRect(grid, 7, 4, 18, 2, color)
            break
        case 11: // Messy
            fillRect(grid, 6, 3, 20, 5, color)
            setPixel(grid, 8, 2, color); setPixel(grid, 14, 1, color); setPixel(grid, 20, 2, color)
            setPixel(grid, 11, 1, color); setPixel(grid, 23, 3, color)
            break
    }
}

// --- Accessories ---
function drawAccessory(grid, style) {
    switch (style) {
        case 0: break // none
        case 1: // Glasses
            fillRect(grid, 8, 13, 6, 4, null) // clear area
            fillRect(grid, 18, 13, 6, 4, null)
            for (let x = 8; x < 14; x++) { setPixel(grid, x, 12, '#888'); setPixel(grid, x, 16, '#888') }
            for (let x = 18; x < 24; x++) { setPixel(grid, x, 12, '#888'); setPixel(grid, x, 16, '#888') }
            setPixel(grid, 8, 13, '#888'); setPixel(grid, 8, 14, '#888'); setPixel(grid, 8, 15, '#888')
            setPixel(grid, 13, 13, '#888'); setPixel(grid, 13, 14, '#888'); setPixel(grid, 13, 15, '#888')
            setPixel(grid, 18, 13, '#888'); setPixel(grid, 18, 14, '#888'); setPixel(grid, 18, 15, '#888')
            setPixel(grid, 23, 13, '#888'); setPixel(grid, 23, 14, '#888'); setPixel(grid, 23, 15, '#888')
            fillRect(grid, 14, 13, 4, 1, '#888') // bridge
            break
        case 2: // Sunglasses
            fillRect(grid, 8, 12, 6, 4, '#111')
            fillRect(grid, 18, 12, 6, 4, '#111')
            fillRect(grid, 14, 13, 4, 1, '#333')
            break
        case 3: // Earring (left)
            setPixel(grid, 5, 16, '#FFD700')
            setPixel(grid, 5, 17, '#FFD700')
            break
        case 4: // Headband
            fillRect(grid, 6, 8, 20, 2, '#ff2244')
            break
        case 5: // Beanie
            fillRect(grid, 6, 2, 20, 6, '#333')
            fillRect(grid, 7, 1, 18, 2, '#333')
            fillRect(grid, 6, 7, 20, 2, '#555')
            break
        case 6: // Eye patch
            fillRect(grid, 8, 12, 6, 5, '#222')
            fillRect(grid, 6, 13, 2, 1, '#222')
            fillRect(grid, 14, 13, 12, 1, '#222')
            break
        case 7: // Scar
            setPixel(grid, 19, 12, '#aa6655'); setPixel(grid, 20, 13, '#aa6655')
            setPixel(grid, 20, 14, '#aa6655'); setPixel(grid, 21, 15, '#aa6655')
            break
    }
}

// --- Clothing ---
function drawClothing(grid, style, color) {
    const y = 27
    switch (style) {
        case 0: // T-shirt
            fillRect(grid, 8, y, 16, 5, color)
            fillRect(grid, 4, y + 1, 4, 4, color)
            fillRect(grid, 24, y + 1, 4, 4, color)
            // Neckline
            fillRect(grid, 14, y, 3, 1, darken(color, 0.7))
            break
        case 1: // Hoodie
            fillRect(grid, 6, y, 20, 5, color)
            fillRect(grid, 3, y + 1, 3, 4, color)
            fillRect(grid, 26, y + 1, 3, 4, color)
            // Hood collar
            fillRect(grid, 12, y, 7, 2, darken(color, 0.8))
            break
        case 2: // Suit
            fillRect(grid, 8, y, 16, 5, color)
            fillRect(grid, 4, y + 1, 4, 4, color)
            fillRect(grid, 24, y + 1, 4, 4, color)
            // Lapels
            setPixel(grid, 13, y + 1, '#ffffff'); setPixel(grid, 17, y + 1, '#ffffff')
            setPixel(grid, 14, y + 2, '#ffffff'); setPixel(grid, 16, y + 2, '#ffffff')
            // Tie
            fillRect(grid, 15, y, 1, 5, '#cc2244')
            break
        case 3: // Tank top
            fillRect(grid, 10, y, 12, 5, color)
            break
        case 4: // Turtleneck
            fillRect(grid, 8, y, 16, 5, color)
            fillRect(grid, 4, y + 1, 4, 4, color)
            fillRect(grid, 24, y + 1, 4, 4, color)
            fillRect(grid, 12, y - 1, 7, 2, color)
            break
        case 5: // V-neck
            fillRect(grid, 8, y, 16, 5, color)
            fillRect(grid, 4, y + 1, 4, 4, color)
            fillRect(grid, 24, y + 1, 4, 4, color)
            setPixel(grid, 14, y, null); setPixel(grid, 16, y, null)
            setPixel(grid, 15, y + 1, null)
            break
    }
}

// --- Utility ---
function darken(hex, factor) {
    const r = parseInt(hex.slice(1, 3), 16)
    const g = parseInt(hex.slice(3, 5), 16)
    const b = parseInt(hex.slice(5, 7), 16)
    return '#' + [r, g, b].map(c => Math.round(c * factor).toString(16).padStart(2, '0')).join('')
}

// --- Score-reactive background ---
function getBackground(score) {
    if (score == null || score < 0) return { color: '#0a0a0f', glow: null }
    if (score >= 80) return { color: '#1a0008', glow: '#ff2244' }
    if (score >= 60) return { color: '#1a0f00', glow: '#ff8800' }
    if (score >= 40) return { color: '#1a1a00', glow: '#ffcc00' }
    if (score >= 20) return { color: '#000a1a', glow: '#3388ff' }
    return { color: '#001a0a', glow: '#00ff88' }
}

// --- Score-reactive expression modifier ---
function modifyExpression(traits, score) {
    if (score == null) return traits
    const t = { ...traits }
    if (score >= 80) t.expression = 3       // angry/worried
    else if (score >= 60) t.expression = 2  // concerned
    else if (score < 20) t.expression = 0   // happy
    return t
}

// --- Glitch effect (high score) ---
function applyGlitch(grid, score, rng) {
    if (score == null || score < 70) return
    const intensity = Math.min(5, Math.floor((score - 70) / 6))
    for (let i = 0; i < intensity; i++) {
        const y = Math.floor(rng() * 32)
        const shift = Math.floor(rng() * 3) + 1
        const dir = rng() > 0.5 ? 1 : -1
        const row = [...grid[y]]
        for (let x = 0; x < 32; x++) {
            const src = x - shift * dir
            grid[y][x] = (src >= 0 && src < 32) ? row[src] : null
        }
    }
}

// --- Main render ---
function renderAvatar(seed, score) {
    const numSeed = seedFromObj(seed)
    const rng = splitmix32(numSeed)

    let traits = selectTraits(rng)
    traits = modifyExpression(traits, score)
    const bg = getBackground(score)

    const grid = createGrid()

    // Draw in correct layer order
    drawClothing(grid, traits.clothing, traits.clothingColor)
    drawFace(grid, traits.faceShape, traits.skin)
    drawNose(grid, traits.nose, traits.skin)
    drawEyes(grid, traits.eyeStyle, traits.eyeColor, traits.expression)
    drawEyebrows(grid, traits.eyebrows, traits.hairColor)
    drawMouth(grid, traits.mouth, traits.expression)
    drawFacialHair(grid, traits.facialHair, traits.hairColor)
    drawHair(grid, traits.hairStyle, traits.hairColor)
    drawAccessory(grid, traits.accessory)

    // Glitch for high-risk targets
    const glitchRng = splitmix32(numSeed + 999)
    applyGlitch(grid, score, glitchRng)

    return { grid, bg }
}

// --- React component ---
export default function GenerativeAvatar({ seed, size = 40, score = null, className = '' }) {
    if (!seed) return null

    const { grid, bg } = renderAvatar(seed, score)
    const pixelSize = size / 32

    // Collect non-null pixels into rect elements
    const pixels = []
    for (let y = 0; y < 32; y++) {
        for (let x = 0; x < 32; x++) {
            if (grid[y][x]) {
                pixels.push(
                    <rect
                        key={`${x}-${y}`}
                        x={x * pixelSize}
                        y={y * pixelSize}
                        width={pixelSize + 0.5}
                        height={pixelSize + 0.5}
                        fill={grid[y][x]}
                    />
                )
            }
        }
    }

    return (
        <svg
            width={size}
            height={size}
            viewBox={`0 0 ${size} ${size}`}
            className={className}
            style={{ imageRendering: 'pixelated' }}
        >
            {/* Background */}
            <rect width={size} height={size} fill={bg.color} rx={size * 0.08} />

            {/* Glow ring for scored targets */}
            {bg.glow && (
                <rect
                    width={size}
                    height={size}
                    fill="none"
                    stroke={bg.glow}
                    strokeWidth={pixelSize * 0.8}
                    strokeOpacity={0.3}
                    rx={size * 0.08}
                />
            )}

            {/* Face pixels */}
            {pixels}
        </svg>
    )
}
