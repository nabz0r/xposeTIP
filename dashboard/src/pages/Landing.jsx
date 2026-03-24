import { useState, useRef, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../lib/auth'
import { PHASES } from '../components/landing/constants'
import HeroSection from '../components/landing/HeroSection'
import ProblemSection from '../components/landing/ProblemSection'
import FeaturesSection from '../components/landing/FeaturesSection'
import PipelineSection from '../components/landing/PipelineSection'
import MockPreview from '../components/landing/MockPreview'
import PricingSection from '../components/landing/PricingSection'
import TrustBar from '../components/landing/TrustBar'
import TechStack from '../components/landing/TechStack'
import FinalCTA from '../components/landing/FinalCTA'
import LandingFooter from '../components/landing/LandingFooter'

export default function Landing() {
  const [email, setEmail] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [quickResult, setQuickResult] = useState(null)
  const [pollCount, setPollCount] = useState(0)
  const { token } = useAuth()
  const navigate = useNavigate()
  const pollRef = useRef(null)

  useEffect(() => {
    return () => { if (pollRef.current) clearInterval(pollRef.current) }
  }, [])

  async function handleQuickScan(e) {
    e.preventDefault()
    if (!email || !email.includes('@')) {
      setError('Enter a valid email address')
      return
    }
    setError('')
    setLoading(true)
    setQuickResult(null)
    setPollCount(0)

    if (token) {
      navigate(`/targets?scan=${encodeURIComponent(email)}`)
      return
    }

    try {
      const resp = await fetch('/api/v1/scan/quick', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email }),
      })

      if (resp.status === 429) {
        setError('Rate limit reached. Create a free account for unlimited scans.')
        setLoading(false)
        return
      }

      if (!resp.ok) {
        const data = await resp.json().catch(() => ({}))
        setError(data.detail || 'Scan failed. Try again.')
        setLoading(false)
        return
      }

      const data = await resp.json()

      if (data.status === 'completed') {
        setQuickResult(data)
        setLoading(false)
        return
      }

      // Poll for results — 300s max
      const scanId = data.scan_id
      let attempts = 0
      pollRef.current = setInterval(async () => {
        attempts++
        setPollCount(attempts)
        try {
          const statusResp = await fetch(`/api/v1/scan/quick/${scanId}/status`)
          const statusData = await statusResp.json()
          if (statusData.status === 'completed') {
            clearInterval(pollRef.current)
            pollRef.current = null
            setQuickResult(statusData)
            setLoading(false)
          } else if (attempts >= 300) {
            clearInterval(pollRef.current)
            pollRef.current = null
            setError('Scan taking longer than expected. Create an account to see results.')
            setLoading(false)
          }
        } catch {
          clearInterval(pollRef.current)
          pollRef.current = null
          setError('Connection error')
          setLoading(false)
        }
      }, 1000)

    } catch {
      setError('Network error. Try again.')
      setLoading(false)
    }
  }

  const phaseMsg = PHASES.find(p => pollCount < p.until)?.msg || 'Finalizing results...'

  return (
    <div className="min-h-screen bg-[#0a0a0f] text-white overflow-x-hidden">
      <style>{`
        @keyframes float {
          0%, 100% { transform: translateY(0px); }
          50% { transform: translateY(-6px); }
        }
        @keyframes fadeInUp {
          from { opacity: 0; transform: translateY(20px); }
          to { opacity: 1; transform: translateY(0); }
        }
      `}</style>

      <HeroSection
        email={email} setEmail={setEmail} loading={loading} error={error}
        onSubmit={handleQuickScan} quickResult={quickResult}
        pollCount={pollCount} phaseMsg={phaseMsg}
      />
      <ProblemSection />
      <FeaturesSection />
      <PipelineSection />
      <MockPreview />
      <PricingSection />
      <TrustBar />
      <TechStack />
      <FinalCTA email={email} setEmail={setEmail} loading={loading} error={error} onSubmit={handleQuickScan} />
      <LandingFooter />
    </div>
  )
}
