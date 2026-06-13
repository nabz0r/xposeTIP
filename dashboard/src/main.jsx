import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import './index.css'
import Layout from './components/Layout'
import Login from './pages/Login'
import Setup from './pages/Setup'
import Dashboard from './pages/Dashboard'
import Targets from './pages/Targets'
import AgentNetwork from './pages/AgentNetwork'
import TargetDetail from './pages/TargetDetail'
import Settings from './pages/Settings'
import Scrapers from './pages/Scrapers'
import System from './pages/System'
import Organization from './pages/Organization'
import Landing from './pages/Landing'
import Architecture from './pages/Architecture'
import UserPreview from './pages/UserPreview'
import Manifesto from './pages/Manifesto'
import BFP from './pages/BFP'
import Compare from './pages/Compare'
import DocLayout from './components/shared/DocLayout'
import Engine from './pages/Engine'
import Demo from './pages/Demo'
import Portal from './pages/Portal'
import Changelog from './pages/Changelog'
import Consulting from './pages/Consulting'
import { AuthProvider, useAuth } from './lib/auth'
import { ToastProvider } from './components/Toast'

function ProtectedRoute({ children }) {
  const { token } = useAuth()
  if (!token) return <Navigate to="/welcome" replace />
  return children
}

function App() {
  return (
    <AuthProvider>
      <ToastProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/welcome" element={<Landing />} />
          <Route path="/manifesto" element={<Manifesto />} />
          {/* S301a — Doc hub (nested) */}
          <Route path="/doc" element={<DocLayout />}>
            <Route index element={<Navigate to="/doc/architecture" replace />} />
            <Route path="architecture" element={<Architecture />} />
            <Route path="bfp" element={<BFP />} />
            <Route path="compare" element={<Compare />} />
            <Route path="engine" element={<Engine />} />
            <Route path="changelog" element={<Changelog />} />
          </Route>
          {/* Legacy redirects — preserve SEO + existing internal links */}
          <Route path="/architecture" element={<Navigate to="/doc/architecture" replace />} />
          <Route path="/bfp" element={<Navigate to="/doc/bfp" replace />} />
          <Route path="/compare" element={<Navigate to="/doc/compare" replace />} />
          <Route path="/changelog" element={<Navigate to="/doc/changelog" replace />} />
          <Route path="/demo" element={<Demo />} />
          <Route path="/portal" element={<Portal />} />
          <Route path="/login" element={<Login />} />
          <Route path="/setup" element={<Setup />} />
          <Route path="/" element={<ProtectedRoute><Layout /></ProtectedRoute>}>
            <Route index element={<Dashboard />} />
            <Route path="targets" element={<Targets />} />
            <Route path="targets/:id" element={<TargetDetail />} />
            <Route path="agent-network" element={<AgentNetwork />} />
            <Route path="organization" element={<Organization />} />
            <Route path="scrapers" element={<Scrapers />} />
            <Route path="system" element={<System />} />
            <Route path="settings" element={<Settings />} />
            <Route path="user-preview" element={<UserPreview />} />
            <Route path="consulting" element={<Consulting />} />
          </Route>
        </Routes>
      </BrowserRouter>
      </ToastProvider>
    </AuthProvider>
  )
}

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)
