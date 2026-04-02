import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { useState, useEffect, useRef, useCallback } from 'react'
import Login from './pages/Login'
import Landing from './pages/Landing'
import ExamPortal from './pages/ExamPortal'
import ProctorDashboard from './pages/ProctorDashboard'
import './styles/tailwind.css'
import './index.css'
import './exam.css'

// ─── Constants ───────────────────────────────────────────────────────────────

const MODULES = [
  { key: 'vision', name: 'Vision', icon: '👁️', color: '#3b82f6' },
  { key: 'behavior', name: 'Behavior', icon: '⌨️', color: '#8b5cf6' },
  { key: 'audio', name: 'Audio', icon: '🎙️', color: '#06b6d4' },
  { key: 'stylometry', name: 'Stylometry', icon: '✍️', color: '#ec4899' },
  { key: 'environmental', name: 'Environment', icon: '🏠', color: '#f59e0b' },
]

function getRiskLevel(score) {
  if (score >= 80) return { label: 'Likely Cheating', class: 'critical', color: '#ef4444' }
  if (score >= 60) return { label: 'High Risk', class: 'high', color: '#f97316' }
  if (score >= 30) return { label: 'Suspicious', class: 'suspicious', color: '#f59e0b' }
  return { label: 'Safe', class: 'safe', color: '#10b981' }
}

function formatTime(timestamp) {
  if (!timestamp) return '--:--'
  const d = new Date(timestamp * 1000)
  return d.toLocaleTimeString('en-US', { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' })
}

// ─── Risk Gauge Component ────────────────────────────────────────────────────

function RiskGauge({ score }) {
  const radius = 80
  const circumference = Math.PI * radius
  const progress = (score / 100) * circumference
  const dashOffset = circumference - progress
  const risk = getRiskLevel(score)

  return (
    <div className="card risk-gauge-container">
      <div className="card-header">
        <span className="card-title"><span className="icon">🎯</span> Risk Score</span>
        <span className={`card-badge ${risk.class}`}>{risk.label}</span>
      </div>
      <div className="gauge-wrapper">
        <svg className="gauge-svg" viewBox="0 0 200 120">
          <path className="gauge-bg" d="M 20 100 A 80 80 0 0 1 180 100" />
          <path className="gauge-fill" d="M 20 100 A 80 80 0 0 1 180 100"
            style={{ stroke: risk.color, strokeDasharray: circumference, strokeDashoffset: dashOffset }} />
          <text x="100" y="85" textAnchor="middle" className="gauge-value">{Math.round(score)}</text>
          <text x="100" y="110" textAnchor="middle" className="gauge-label">out of 100</text>
        </svg>
        <span className={`risk-level-text ${risk.class}`}>{risk.label}</span>
      </div>
    </div>
  )
}

// ─── Module Scores ───────────────────────────────────────────────────────────

function ModuleScores({ scores }) {
  return (
    <div className="card module-scores-container">
      <div className="card-header">
        <span className="card-title"><span className="icon">📊</span> Module Breakdown</span>
      </div>
      <div className="module-grid">
        {MODULES.map((mod) => {
          const score = scores[mod.key]?.score ?? 0
          const pct = Math.round(score * 100)
          const risk = getRiskLevel(pct)
          return (
            <div className="module-card" key={mod.key}>
              <div className="module-icon">{mod.icon}</div>
              <div className="module-name">{mod.name}</div>
              <div className="module-score" style={{ color: risk.color }}>{pct}</div>
              <div className="module-bar">
                <div className="module-bar-fill" style={{ width: `${pct}%`, background: risk.color, boxShadow: `0 0 8px ${risk.color}40` }} />
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}

// ─── Timeline ────────────────────────────────────────────────────────────────

function TimelineChart({ timeline }) {
  const canvasRef = useRef(null)
  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return
    const ctx = canvas.getContext('2d')
    const w = canvas.width = canvas.parentElement.clientWidth
    const h = canvas.height = 200
    ctx.clearRect(0, 0, w, h)

    ctx.strokeStyle = 'rgba(148, 163, 184, 0.08)'
    ctx.lineWidth = 1
    for (let y = 0; y <= 100; y += 25) {
      const py = h - (y / 100) * h
      ctx.beginPath(); ctx.moveTo(0, py); ctx.lineTo(w, py); ctx.stroke()
      ctx.fillStyle = '#64748b'; ctx.font = '10px JetBrains Mono'; ctx.textAlign = 'right'
      ctx.fillText(y.toString(), 28, py + 4)
    }

    const data = timeline.slice(-100)
    if (data.length < 2) return
    const xStep = (w - 40) / 99
    const lastScore = data[data.length - 1]?.score ?? 0
    const riskColor = getRiskLevel(lastScore).color

    const gradient = ctx.createLinearGradient(0, 0, 0, h)
    gradient.addColorStop(0, riskColor + '40'); gradient.addColorStop(1, riskColor + '00')
    ctx.beginPath(); ctx.moveTo(40, h)
    data.forEach((p, i) => { const x = 40 + i * xStep; const y = h - (p.score / 100) * h; i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y) })
    ctx.lineTo(40 + (data.length - 1) * xStep, h); ctx.closePath(); ctx.fillStyle = gradient; ctx.fill()

    ctx.beginPath()
    data.forEach((p, i) => { const x = 40 + i * xStep; const y = h - (p.score / 100) * h; i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y) })
    ctx.strokeStyle = riskColor; ctx.lineWidth = 2; ctx.shadowColor = riskColor; ctx.shadowBlur = 8; ctx.stroke(); ctx.shadowBlur = 0

    const li = data.length - 1; const lx = 40 + li * xStep; const ly = h - (data[li].score / 100) * h
    ctx.beginPath(); ctx.arc(lx, ly, 5, 0, Math.PI * 2); ctx.fillStyle = riskColor; ctx.fill()
    ctx.strokeStyle = '#0a0e1a'; ctx.lineWidth = 2; ctx.stroke()
  }, [timeline])

  return (
    <div className="card timeline-container">
      <div className="card-header">
        <span className="card-title"><span className="icon">📈</span> Risk Timeline</span>
        <span className="card-badge safe">{timeline.length} samples</span>
      </div>
      <div className="chart-area"><canvas ref={canvasRef} className="chart-canvas" /></div>
    </div>
  )
}

// ─── Events ──────────────────────────────────────────────────────────────────

function EventsPanel({ events }) {
  const listRef = useRef(null)
  useEffect(() => { if (listRef.current) listRef.current.scrollTop = 0 }, [events.length])
  const sev = (s) => s >= 0.8 ? 'severity-critical' : s >= 0.6 ? 'severity-high' : s >= 0.4 ? 'severity-medium' : 'severity-low'
  return (
    <div className="card events-container">
      <div className="card-header">
        <span className="card-title"><span className="icon">🚨</span> Anomaly Events</span>
        <span className="card-badge suspicious">{events.length}</span>
      </div>
      {events.length === 0 ? (
        <div className="empty-state"><span className="icon">✅</span><p>No anomalies detected</p></div>
      ) : (
        <div className="events-list" ref={listRef}>
          {[...events].reverse().slice(0, 20).map((e, i) => (
            <div className={`event-item ${sev(e.severity)}`} key={i}>
              <div><div className="event-time">{formatTime(e.timestamp)}</div><span className="event-module">{e.module}</span></div>
              <div className="event-text">{e.description}</div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

// ─── Explanation ─────────────────────────────────────────────────────────────

function ExplanationPanel({ explanation }) {
  if (!explanation) return null
  return (
    <div className="card explanation-container">
      <div className="card-header">
        <span className="card-title"><span className="icon">🧠</span> Explainable AI Panel</span>
      </div>
      <div className="explanation-grid">
        <div className="explanation-item"><h4>📋 Assessment</h4><p>{explanation.explanation || 'No data yet'}</p></div>
        <div className="explanation-item">
          <h4>🔍 Top Contributors</h4>
          {explanation.top_contributors?.length ? (
            <div>{explanation.top_contributors.map((c, i) => (
              <div key={i} style={{ marginBottom: '6px' }}>
                <span className="explanation-module-tag" style={{ background: `${MODULES.find(m => m.key === c.module)?.color || '#3b82f6'}20`, color: MODULES.find(m => m.key === c.module)?.color || '#3b82f6' }}>{c.module}</span>
                <span style={{ fontSize: '0.85rem', color: '#94a3b8' }}>{c.contribution?.toFixed(1)} pts (weight: {c.weight})</span>
              </div>
            ))}</div>
          ) : <p style={{ color: '#64748b' }}>No significant contributors</p>}
        </div>
        <div className="explanation-item"><h4>💡 Recommendation</h4><p>{explanation.recommendation || 'Monitoring...'}</p></div>
      </div>
    </div>
  )
}

// ─── Demo Simulation ─────────────────────────────────────────────────────────

function useDemoMode() {
  const [isRunning, setIsRunning] = useState(false)
  const [riskScore, setRiskScore] = useState(0)
  const [moduleScores, setModuleScores] = useState({})
  const [timeline, setTimeline] = useState([])
  const [events, setEvents] = useState([])
  const [explanation, setExplanation] = useState(null)
  const intervalRef = useRef(null)
  const tickRef = useRef(0)

  const generateScores = useCallback(() => {
    tickRef.current++
    const t = tickRef.current
    const spike = Math.random() > 0.85; const bigSpike = Math.random() > 0.95
    const newScores = {}
    MODULES.forEach(mod => {
      let base = 0.05 + Math.random() * 0.15
      if (spike) base += Math.random() * 0.3; if (bigSpike) base += Math.random() * 0.5
      base += 0.05 * Math.sin(t * 0.1 + MODULES.indexOf(mod))
      newScores[mod.key] = { score: Math.min(Math.max(base, 0), 1), confidence: 0.6 + Math.random() * 0.3 }
    })
    setModuleScores(newScores)

    const weights = { vision: 0.25, behavior: 0.20, audio: 0.20, stylometry: 0.20, environmental: 0.15 }
    let overall = 0
    Object.entries(weights).forEach(([k, w]) => { overall += w * (newScores[k]?.score ?? 0) * 100 })
    setRiskScore(prev => 0.3 * overall + 0.7 * prev)
    setTimeline(prev => [...prev, { score: 0.3 * overall + 0.7 * (prev[prev.length - 1]?.score || 0), timestamp: Date.now() / 1000 }].slice(-100))

    if (spike || bigSpike) {
      const mod = MODULES[Math.floor(Math.random() * MODULES.length)]
      const sev = bigSpike ? 0.7 + Math.random() * 0.3 : 0.4 + Math.random() * 0.3
      const descs = { vision: ['Gaze deviation', 'Downward glance', 'Illumination change'], behavior: ['Typing burst', 'Copy-paste', 'Rhythm change'], audio: ['Whisper detected', 'Room change', 'Voice spike'], stylometry: ['Style shift', 'Vocab jump', 'AI pattern'], environmental: ['Noise change', 'Background activity'] }
      setEvents(prev => [...prev.slice(-49), { module: mod.key, severity: sev, description: (descs[mod.key] || ['Anomaly'])[Math.floor(Math.random() * (descs[mod.key]?.length || 1))], timestamp: Date.now() / 1000 }])
    }

    const risk = getRiskLevel(0.3 * overall + 0.7 * (riskScore || 0))
    const sorted = Object.entries(newScores).sort((a, b) => b[1].score - a[1].score)
    setExplanation({
      explanation: `Risk ${Math.round(0.3 * overall + 0.7 * (riskScore || 0))}/100 — ${risk.label}`,
      top_contributors: sorted.slice(0, 3).map(([k, v]) => ({ module: k, contribution: v.score * (weights[k] || 0.2) * 100, weight: weights[k] || 0.2 })),
      recommendation: risk.class === 'safe' ? 'No action needed.' : risk.class === 'suspicious' ? 'Monitor closely.' : risk.class === 'high' ? 'Review recommended.' : 'Immediate review required.'
    })
  }, [riskScore])

  const start = useCallback(() => { setIsRunning(true); setRiskScore(0); setModuleScores({}); setTimeline([]); setEvents([]); tickRef.current = 0; intervalRef.current = setInterval(generateScores, 800) }, [generateScores])
  const stop = useCallback(() => { setIsRunning(false); if (intervalRef.current) clearInterval(intervalRef.current) }, [])
  useEffect(() => () => { if (intervalRef.current) clearInterval(intervalRef.current) }, [])
  return { isRunning, riskScore, moduleScores, timeline, events, explanation, start, stop }
}

// ─── Admin Dashboard (original) ──────────────────────────────────────────────

function AdminDashboard() {
  const [studentId, setStudentId] = useState('')
  const [sessionId, setSessionId] = useState(null)
  const [connected, setConnected] = useState(false)
  const demo = useDemoMode()

  const handleStart = () => { setSessionId('demo-session'); setConnected(true); demo.start() }
  const handleStop = () => { setConnected(false); demo.stop(); setSessionId(null) }

  return (
    <div className="app-container animate-fade-in">
      <header className="header">
        <div className="header-brand">
          <div className="header-logo">T</div>
          <div><div className="header-title">TrustIQ Dashboard</div><div className="header-subtitle">AI Behavioural Integrity Engine</div></div>
        </div>
        <div className="header-status">
          <div className="status-indicator"><div className={`status-dot ${connected ? '' : 'offline'}`} /><span>{connected ? 'Live' : 'Offline'}</span></div>
          {sessionId && <div className="status-indicator" style={{ fontFamily: 'JetBrains Mono', fontSize: '0.75rem' }}>📋 {sessionId.slice(0, 12)}...</div>}
        </div>
      </header>
      <div className="controls">
        <input className="input" placeholder="Student ID" value={studentId} onChange={(e) => setStudentId(e.target.value)} />
        {!demo.isRunning ? <button className="btn btn-primary" onClick={handleStart}>🚀 Start Demo</button> : <button className="btn btn-danger" onClick={handleStop}>⏹️ Stop</button>}
      </div>
      <main className="dashboard animate-slide-up delay-200">
        <RiskGauge score={demo.riskScore} />
        <ModuleScores scores={demo.moduleScores} />
        <TimelineChart timeline={demo.timeline} />
        <EventsPanel events={demo.events} />
        <ExplanationPanel explanation={demo.explanation} />
      </main>
    </div>
  )
}

// ─── Main App Router ─────────────────────────────────────────────────────────

function App() {
  const [, setUser] = useState(null)

  useEffect(() => {
    // Dynamic import to avoid crash when Firebase is unconfigured
    import('./firebase').then(({ auth }) => {
      if (auth) {
        import('firebase/auth').then(({ onAuthStateChanged }) => {
          onAuthStateChanged(auth, (u) => setUser(u || null))
        })
      }
    }).catch(() => {
      // Firebase not configured, stay in demo mode
    })
  }, [])

  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Landing />} />
        <Route path="/login" element={<Login />} />
        <Route path="/exam" element={<ExamPortal />} />
        <Route path="/proctor" element={<ProctorDashboard />} />
        <Route path="/dashboard" element={<ProctorDashboard />} />
        <Route path="/demo-dashboard" element={<AdminDashboard />} />
        <Route path="*" element={<Navigate to="/" />} />
      </Routes>
    </BrowserRouter>
  )
}

export default App
