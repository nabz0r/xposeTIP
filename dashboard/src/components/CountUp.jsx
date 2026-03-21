import { useState, useEffect, useRef } from 'react'

/**
 * CountUp — scroll-triggered number animation.
 * Counts from 0 to target when element scrolls into view.
 */
export default function CountUp({ target, duration = 2000, suffix = '' }) {
    const [count, setCount] = useState(0)
    const ref = useRef(null)
    const started = useRef(false)

    useEffect(() => {
        const observer = new IntersectionObserver(([entry]) => {
            if (entry.isIntersecting && !started.current) {
                started.current = true
                const start = Date.now()
                const timer = setInterval(() => {
                    const elapsed = Date.now() - start
                    const progress = Math.min(1, elapsed / duration)
                    // Ease out cubic
                    const eased = 1 - Math.pow(1 - progress, 3)
                    setCount(Math.round(target * eased))
                    if (progress >= 1) clearInterval(timer)
                }, 16)
            }
        }, { threshold: 0.5 })

        if (ref.current) observer.observe(ref.current)
        return () => observer.disconnect()
    }, [target, duration])

    return <span ref={ref}>{count}{suffix}</span>
}
