import { useState, useRef, useEffect } from 'react'

export default function LiveCounter() {
  const [count, setCount] = useState(4_237_891_442)
  const ref = useRef(null)
  const [started, setStarted] = useState(false)

  useEffect(() => {
    const observer = new IntersectionObserver(
      ([entry]) => { if (entry.isIntersecting) setStarted(true) },
      { threshold: 0.3 }
    )
    if (ref.current) observer.observe(ref.current)
    return () => observer.disconnect()
  }, [])

  useEffect(() => {
    if (!started) return
    const interval = setInterval(() => {
      setCount(c => c + Math.floor(Math.random() * 3) + 12)
    }, 1000)
    return () => clearInterval(interval)
  }, [started])

  return (
    <div ref={ref}>
      <div className="text-6xl md:text-8xl font-mono font-bold text-[#ff2244] tabular-nums">
        {count.toLocaleString()}
      </div>
      <p className="text-lg text-gray-400 mt-4">
        records leaked — and counting.
      </p>
      <p className="text-sm text-gray-600 mt-2">
        +13 every second. While you're reading this.
      </p>
    </div>
  )
}
