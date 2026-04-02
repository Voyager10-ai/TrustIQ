import { useState, useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'

function getRiskLevel(score) {
    if (score >= 80) return { label: 'Flagged', color: '#ef4444', text: 'text-red-500', bg: 'bg-red-500/10', border: 'border-red-500/20', icon: '🔴' }
    if (score >= 40) return { label: 'Suspicious', color: '#f59e0b', text: 'text-amber-500', bg: 'bg-amber-500/10', border: 'border-amber-500/20', icon: '🟡' }
    return { label: 'Active', color: '#10b981', text: 'text-emerald-500', bg: 'bg-emerald-500/10', border: 'border-emerald-500/20', icon: '🟢' }
}

const EXAMS = ['CAI-101 Midterm', 'PHY-202 Final', 'ENG-105 Quiz']
const EVENT_TYPES = [
    'Looking away frequently',
    'Multiple faces detected',
    'No face detected',
    'Tab switching detected',
    'Background noise detected',
    'Whispering detected'
]

function generateMockStudents() {
    const names = [
        'Pradnyesh K.', 'Ananya S.', 'Rohit M.', 'Priya G.', 'Aditya V.',
        'Neha P.', 'Karan J.', 'Shreya T.', 'Vikram R.', 'Pooja D.',
        'Rahul N.', 'Meera B.'
    ]
    return names.map((name, i) => {
        const riskScore = Math.random() * 40
        const id = `24BAI${70600 + i}`
        const startTime = new Date(Date.now() - Math.random() * 7200000)

        const events = []
        if (Math.random() > 0.5) {
            const numEvents = Math.floor(Math.random() * 3) + 1
            for (let e = 0; e < numEvents; e++) {
                events.push({
                    id: Math.random().toString(36).substring(7),
                    type: EVENT_TYPES[Math.floor(Math.random() * EVENT_TYPES.length)],
                    time: new Date(Date.now() - Math.random() * 1800000).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })
                })
            }
        }

        return {
            id,
            name,
            examName: EXAMS[Math.floor(Math.random() * EXAMS.length)],
            riskScore,
            loginTime: startTime.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
            events,
            connected: Math.random() > 0.1,
            // mock historical points for the live graph
            history: Array.from({ length: 20 }, () => Math.max(0, Math.min(100, riskScore + (Math.random() - 0.5) * 20))),
            isMock: true
        }
    })
}

// Simple sparkline component
const Sparkline = ({ data, color }) => {
    const min = Math.min(...data)
    const max = Math.max(...data)
    const pts = data.map((d, i) => `${i * (100 / (data.length - 1))},${100 - ((d - min) / (max - min || 1)) * 100}`).join(' L')
    return (
        <svg className="w-full h-full overflow-visible" preserveAspectRatio="none" viewBox="0 0 100 100">
            <path d={`M${pts}`} fill="none" stroke={color} strokeWidth="3" vectorEffect="non-scaling-stroke" strokeLinecap="round" strokeLinejoin="round" />
            <path d={`M0,100 L${pts} L100,100 Z`} fill={`url(#grad-${color.replace('#', '')})`} opacity="0.2" />
            <defs>
                <linearGradient id={`grad-${color.replace('#', '')}`} x1="0" x2="0" y1="0" y2="1">
                    <stop offset="0%" stopColor={color} stopOpacity="1" />
                    <stop offset="100%" stopColor={color} stopOpacity="0" />
                </linearGradient>
            </defs>
        </svg>
    )
}

export default function ProctorDashboard() {
    const navigate = useNavigate()
    const [students, setStudents] = useState(generateMockStudents())
    const [selectedStudent, setSelectedStudent] = useState(null)
    const [searchTerm, setSearchTerm] = useState('')
    const [filterStatus, setFilterStatus] = useState('All')
    const [filterExam, setFilterExam] = useState('All')
    const [globalAlert, setGlobalAlert] = useState(null)

    const intervalRef = useRef(null)

    // Simulate live updates & fetch real data
    useEffect(() => {
        intervalRef.current = setInterval(async () => {
            let realSessions = []
            try {
                const res = await fetch('http://localhost:8000/ws/active-sessions')
                if (res.ok) {
                    const data = await res.json()
                    realSessions = data.sessions || []
                }
            } catch {
                // Ignore network errors for mock mode
            }

            setStudents(prev => {
                // 1. Process mock students
                const updatedMock = prev.filter(s => s.isMock).map(s => {
                    const spike = Math.random() > 0.95
                    const change = (Math.random() - 0.5) * 8
                    const newRisk = Math.max(0, Math.min(100, s.riskScore + change + (spike ? 25 : 0)))

                    const newEvents = [...s.events]
                    if (spike) {
                        newEvents.unshift({
                            id: Math.random().toString(36).substring(7),
                            type: EVENT_TYPES[Math.floor(Math.random() * EVENT_TYPES.length)],
                            time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })
                        })
                        if (newRisk >= 80) {
                            setGlobalAlert(`🚨 High Risk Detected: ${s.id} (${s.name})`)
                            setTimeout(() => setGlobalAlert(null), 5000)
                        }
                    }

                    return {
                        ...s,
                        riskScore: newRisk,
                        history: [...s.history.slice(1), newRisk],
                        events: newEvents
                    }
                })

                // 2. Process real students
                const updatedReal = realSessions.map(rs => {
                    const existing = prev.find(p => p.id === rs.session_id)
                    const newEvents = existing ? [...existing.events] : []

                    // Add real events based on tracking
                    if (rs.active_tracking?.prohibited_object_detected || rs.active_tracking?.multiple_faces || rs.active_tracking?.no_face_detected) {
                        newEvents.unshift({
                            id: Math.random().toString(36).substring(7),
                            type: rs.active_tracking.multiple_faces ? 'Multiple faces detected' : (rs.active_tracking.no_face_detected ? 'No face detected' : 'Prohibited item detected'),
                            time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })
                        })
                        if (rs.risk_score >= 80) {
                            setGlobalAlert(`🚨 High Risk Detected: ${rs.session_id}`)
                            setTimeout(() => setGlobalAlert(null), 5000)
                        }
                    }

                    return {
                        id: rs.session_id,
                        name: rs.session_id.split('-').slice(0, 2).join('-'), // Make a readable name from session ID
                        examName: 'Live ABIE Exam',
                        riskScore: rs.risk_score,
                        loginTime: 'Active Now',
                        events: newEvents.slice(0, 20),
                        connected: true,
                        history: existing ? [...existing.history.slice(1), rs.risk_score] : Array(20).fill(rs.risk_score),
                        latestFrame: rs.latest_frame,
                        isMock: false
                    }
                })

                return [...updatedReal, ...updatedMock]
            })
        }, 2000)
        return () => clearInterval(intervalRef.current)
    }, [])

    const filteredStudents = students.filter(s => {
        const matchesSearch = s.name.toLowerCase().includes(searchTerm.toLowerCase()) || s.id.toLowerCase().includes(searchTerm.toLowerCase())
        const risk = getRiskLevel(s.riskScore)
        const matchesStatus = filterStatus === 'All' || risk.label === filterStatus
        const matchesExam = filterExam === 'All' || s.examName === filterExam
        return matchesSearch && matchesStatus && matchesExam
    }).sort((a, b) => b.riskScore - a.riskScore)

    const flaggedCount = students.filter(s => s.riskScore >= 80).length
    const avgRisk = Math.round(students.reduce((a, s) => a + s.riskScore, 0) / (students.length || 1))
    const systemRiskLabel = getRiskLevel(avgRisk)

    // Ensure selectedStudent stays updated with live data wrapper
    const currentSelected = selectedStudent ? students.find(s => s.id === selectedStudent.id) : null

    const handleAction = (action) => {
        alert(`${action} triggered for ${currentSelected.name}`)
    }

    return (
        <div className="min-h-screen bg-[#020202] text-slate-200 font-sans p-4 md:p-6 lg:p-8 animate-fade-in flex flex-col">
            {/* Global Alert Notification */}
            {globalAlert && (
                <div className="fixed top-6 left-1/2 -translate-x-1/2 z-50 bg-red-500/90 text-white px-6 py-3 rounded-lg shadow-2xl shadow-red-500/20 backdrop-blur-md border border-red-400 font-semibold animate-slide-up flex items-center gap-3">
                    <span className="text-xl">⚠️</span>
                    {globalAlert}
                </div>
            )}

            {/* Header */}
            <header className="flex flex-col md:flex-row items-start md:items-center justify-between mb-8 pb-6 border-b border-white/5 animate-slide-up">
                <div className="flex items-center gap-4 mb-4 md:mb-0">
                    <div className="w-12 h-12 bg-gradient-to-br from-brand-500 to-emerald-400 rounded-xl flex items-center justify-center text-xl font-bold shadow-lg shadow-brand-500/20">T</div>
                    <div>
                        <h1 className="text-2xl font-bold bg-gradient-to-r from-white to-slate-400 bg-clip-text text-transparent">TrustIQ Proctor Intelligence Dashboard</h1>
                        <p className="text-slate-400 text-sm">AI-Based Behavioural Anomaly Detection & Live Logging</p>
                    </div>
                </div>
                <button onClick={() => navigate('/')} className="px-5 py-2.5 rounded-lg border border-white/10 hover:bg-white/5 transition font-medium text-sm flex items-center gap-2">
                    Logout
                </button>
            </header>

            <div className="flex-1 grid lg:grid-cols-12 gap-8 animate-slide-up delay-100">

                {/* LEFT COLUMN: Global Stats & Live Activity Graph */}
                <div className="lg:col-span-3 flex flex-col gap-6">
                    <div className="bg-[#080808] rounded-xl border border-white/5 p-5 shadow-xl">
                        <h3 className="text-sm font-semibold text-slate-400 uppercase tracking-wide mb-4 flex items-center gap-2">
                            <span>📊</span> Global Metrics
                        </h3>
                        <div className="grid grid-cols-2 gap-4 mb-6">
                            <div className="bg-[#020202] p-4 rounded-lg border border-white/5 flex flex-col items-center justify-center">
                                <span className="text-3xl font-bold font-mono">{students.length}</span>
                                <span className="text-xs text-slate-500 uppercase mt-1">Total Active</span>
                            </div>
                            <div className="bg-[#020202] p-4 rounded-lg border border-red-500/20 flex flex-col items-center justify-center">
                                <span className="text-3xl font-bold font-mono text-red-500">{flaggedCount}</span>
                                <span className="text-xs text-red-500/70 uppercase mt-1">Flagged</span>
                            </div>
                            <div className="col-span-2 bg-[#020202] p-4 rounded-lg border border-white/5 flex flex-col items-center justify-center">
                                <span className={`text-4xl font-bold font-mono ${systemRiskLabel.text}`}>{avgRisk}%</span>
                                <span className="text-xs text-slate-500 uppercase mt-1">Avg System RiskScore</span>
                            </div>
                        </div>

                        <h3 className="text-sm font-semibold text-slate-400 uppercase tracking-wide mb-4 mt-8">Live Activity Graph</h3>
                        <div className="h-32 bg-[#020202] rounded-lg border border-white/5 p-2 px-0 w-full relative">
                            {/* Average Risk history line graph */}
                            <Sparkline data={students[0].history} color={systemRiskLabel.color} />
                        </div>
                    </div>

                    <div className="bg-[#080808] rounded-xl border border-white/5 p-5 flex-1 shadow-xl">
                        <h3 className="text-sm font-semibold text-slate-400 uppercase tracking-wide mb-4 flex items-center gap-2">
                            <span>⚡</span> Face & Gaze Logs (System)
                        </h3>
                        <ul className="space-y-3 max-h-48 overflow-y-auto pr-2 custom-scrollbar">
                            {students.flatMap(s => s.events.map(e => ({ ...e, sId: s.id, name: s.name }))).sort((a, b) => b.time.localeCompare(a.time)).slice(0, 10).map((ev, i) => (
                                <li key={i} className="text-xs border-l-2 border-amber-500/50 pl-3 py-1 bg-[#020202]/50 flex flex-col gap-1">
                                    <span className="text-amber-500/80 font-mono">{ev.time} — {ev.sId}</span>
                                    <span className="text-slate-300 truncate">{ev.type}</span>
                                </li>
                            ))}
                        </ul>
                    </div>
                </div>

                {/* MIDDLE COLUMN: Student List & Filter */}
                <div className="lg:col-span-5 flex flex-col gap-4">
                    <div className="bg-[#080808] rounded-xl border border-white/5 p-4 flex flex-col gap-3 shadow-xl">
                        <div className="relative">
                            <span className="absolute left-3 top-1/2 -translate-y-1/2 opacity-50">🔍</span>
                            <input
                                type="text"
                                placeholder="Search by Student ID or Name..."
                                className="w-full bg-[#020202] border border-white/10 rounded-lg py-2.5 pl-10 pr-4 text-sm focus:outline-none focus:border-brand-500/50 transition-colors"
                                value={searchTerm}
                                onChange={e => setSearchTerm(e.target.value)}
                            />
                        </div>
                        <div className="flex gap-3">
                            <select
                                className="flex-1 bg-[#020202] border border-white/10 rounded-lg py-2.5 px-3 text-sm focus:outline-none focus:border-brand-500/50 appearance-none text-slate-300"
                                value={filterStatus}
                                onChange={e => setFilterStatus(e.target.value)}
                            >
                                <option value="All">All Statuses</option>
                                <option value="Flagged">Flagged</option>
                                <option value="Suspicious">Suspicious</option>
                                <option value="Active">Active</option>
                            </select>
                            <select
                                className="flex-1 bg-[#020202] border border-white/10 rounded-lg py-2.5 px-3 text-sm focus:outline-none focus:border-brand-500/50 appearance-none text-slate-300"
                                value={filterExam}
                                onChange={e => setFilterExam(e.target.value)}
                            >
                                <option value="All">All Exams</option>
                                {EXAMS.map(e => <option key={e} value={e}>{e}</option>)}
                            </select>
                        </div>
                    </div>

                    <div className="flex-1 bg-[#080808] rounded-xl border border-white/5 flex flex-col shadow-xl overflow-hidden min-h-[500px]">
                        <div className="grid grid-cols-[1.5fr_1fr_1fr_0.8fr] gap-4 p-4 border-b border-white/5 text-xs font-semibold text-slate-400 uppercase tracking-wider bg-white/[0.01]">
                            <span>Student</span>
                            <span>Exam & Time</span>
                            <span>Status</span>
                            <span className="text-right">Live Risk</span>
                        </div>
                        <div className="flex-1 overflow-y-auto custom-scrollbar p-2 space-y-2">
                            {filteredStudents.map(student => {
                                const rLabel = getRiskLevel(student.riskScore)
                                const isSelected = currentSelected?.id === student.id
                                return (
                                    <div
                                        key={student.id}
                                        onClick={() => setSelectedStudent(student)}
                                        className={`grid grid-cols-[1.5fr_1fr_1fr_0.8fr] gap-4 p-3 rounded-lg cursor-pointer items-center border transition-all duration-200
                                            ${isSelected ? 'bg-brand-500/10 border-brand-500/30 shadow-lg shadow-brand-500/5' : 'bg-[#020202] border-white/5 hover:border-white/10 hover:bg-white/[0.02]'}
                                        `}
                                    >
                                        <div className="flex items-center gap-3 truncate">
                                            {student.latestFrame ? (
                                                <img src={student.latestFrame.startsWith('data:') ? student.latestFrame : `data:image/jpeg;base64,${student.latestFrame}`} alt="Student" className="w-10 h-10 rounded-md object-cover border border-white/20 shrink-0" />
                                            ) : (
                                                <div className="w-10 h-10 rounded-md bg-slate-800 flex items-center justify-center shrink-0 border border-white/10 text-xl font-bold">{student.name.charAt(0)}</div>
                                            )}
                                            <div className="flex flex-col truncate">
                                                <span className="font-semibold text-slate-200 truncate">{student.name}</span>
                                                <span className="text-xs text-slate-500 font-mono mt-0.5">{student.isMock ? student.id : 'Live Session'}</span>
                                            </div>
                                        </div>
                                        <div className="flex flex-col truncate">
                                            <span className="text-xs text-slate-300 truncate">{student.examName}</span>
                                            <span className="text-[10px] text-slate-500 mt-0.5">{student.loginTime}</span>
                                        </div>
                                        <div className="flex items-center">
                                            <span className={`text-xs px-2 py-1 rounded-md border flex items-center gap-1.5 ${rLabel.bg} ${rLabel.border} ${rLabel.text} font-medium tracking-wide`}>
                                                <span className="text-[10px]">{rLabel.icon}</span> {rLabel.label}
                                            </span>
                                        </div>
                                        <div className="text-right flex flex-col items-end">
                                            <span className={`text-xl font-bold font-mono ${rLabel.text}`}>{Math.round(student.riskScore)}%</span>
                                        </div>
                                    </div>
                                )
                            })}
                        </div>
                    </div>
                </div>

                {/* RIGHT COLUMN: Real-Time Detailed Panel */}
                <div className="lg:col-span-4 flex flex-col gap-6">
                    {currentSelected ? (() => {
                        const sLabel = getRiskLevel(currentSelected.riskScore)
                        return (
                            <div className="animate-fade-in flex flex-col gap-4 h-full overflow-y-auto pr-2 custom-scrollbar">
                                {/* Header */}
                                <div className="bg-[#080808] rounded-xl border border-white/5 p-4 shadow-xl flex justify-between items-center shrink-0">
                                    <div>
                                        <div className="flex items-center gap-3">
                                            <h2 className="text-xl font-bold">{currentSelected.name}</h2>
                                            <span className={`px-2 py-0.5 rounded text-xs font-bold border ${sLabel.border} ${sLabel.text} ${sLabel.bg}`}>{sLabel.label}</span>
                                        </div>
                                        <p className="text-slate-400 font-mono text-sm mt-1">{currentSelected.id} • {currentSelected.examName}</p>
                                    </div>
                                    <button onClick={() => setSelectedStudent(null)} className="opacity-60 hover:opacity-100 p-2 rounded hover:bg-white/10 transition">✕ Close</button>
                                </div>

                                {/* Main Live Camera Feed */}
                                <div className="bg-[#080808] rounded-xl border border-white/5 p-4 shadow-xl shrink-0">
                                    <div className="relative w-full aspect-video bg-black/50 rounded-lg overflow-hidden border border-white/10">
                                        {currentSelected.latestFrame ? (
                                            <>
                                                <img src={currentSelected.latestFrame.startsWith('data:') ? currentSelected.latestFrame : `data:image/jpeg;base64,${currentSelected.latestFrame}`} className="absolute inset-0 w-full h-full object-cover" alt="Live Exam Feed" />
                                                {currentSelected.active_tracking?.objects?.length > 0 && currentSelected.active_tracking.objects.map((obj, i) => (
                                                    <div key={i} className={`absolute border-2 ${obj.color} rounded pointer-events-none shadow-xl`} style={{
                                                        left: `${obj.box.xmin * 100}%`,
                                                        top: `${obj.box.ymin * 100}%`,
                                                        width: `${obj.box.width * 100}%`,
                                                        height: `${obj.box.height * 100}%`,
                                                    }}>
                                                        <span className={`absolute -top-5 left-0 text-[10px] font-bold px-1.5 py-0.5 rounded ${obj.bg} ${obj.color.split(' ')[0]} whitespace-nowrap backdrop-blur-md`}>
                                                            {obj.label}
                                                        </span>
                                                    </div>
                                                ))}
                                            </>
                                        ) : (
                                            <div className="absolute inset-0 flex items-center justify-center text-slate-500 font-mono text-sm">Waiting for video stream...</div>
                                        )}
                                        <div className="absolute top-3 left-3 bg-black/60 backdrop-blur-md text-[10px] font-mono px-2 py-1 rounded text-emerald-400 border border-emerald-500/20 flex items-center gap-2">
                                            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
                                            LIVE WORKSPACE
                                        </div>
                                    </div>
                                </div>

                                {/* Suspicion Meter Panel */}
                                <div className="bg-[#080808] rounded-xl border border-white/5 p-5 shadow-xl relative overflow-hidden shrink-0">
                                    <div className="absolute top-0 left-0 w-full h-1">
                                        <div className="h-full transition-all duration-1000" style={{ width: `${currentSelected.riskScore}%`, backgroundColor: sLabel.color }} />
                                    </div>

                                    <div className="flex items-center gap-6 mb-6">
                                        <div className="relative w-24 h-24 flex items-center justify-center shrink-0">
                                            <svg className="w-full h-full transform -rotate-90 relative z-10">
                                                <circle cx="48" cy="48" r="40" fill="none" stroke="rgba(255,255,255,0.05)" strokeWidth="10" />
                                                <circle cx="48" cy="48" r="40" fill="none" stroke={sLabel.color} strokeWidth="10" strokeDasharray="251" strokeDashoffset={251 - (251 * currentSelected.riskScore / 100)} className="transition-all duration-1000 ease-out" strokeLinecap="round" />
                                            </svg>
                                            <div className="absolute flex flex-col items-center">
                                                <span className={`text-2xl font-bold font-mono ${sLabel.text}`}>{Math.round(currentSelected.riskScore)}<span className="text-sm opacity-50">%</span></span>
                                            </div>
                                        </div>
                                        <div className="flex-1">
                                            <h4 className="text-xs uppercase tracking-wider text-slate-500 mb-2 font-semibold">Risk Analysis Factors</h4>
                                            <ul className="space-y-1.5">
                                                {currentSelected.events.slice(0, 3).map((e, i) => (
                                                    <li key={i} className="text-xs text-slate-300 flex items-start gap-2">
                                                        <span className="text-amber-500 mt-0.5 text-[10px]">⚠️</span>
                                                        <span className="leading-tight">{e.type}</span>
                                                    </li>
                                                ))}
                                                {currentSelected.events.length === 0 && (
                                                    <li className="text-xs text-emerald-500 flex items-center gap-2">
                                                        <span>✅</span> No suspicious behavior detected.
                                                    </li>
                                                )}
                                            </ul>
                                        </div>
                                    </div>

                                    {/* Action Buttons */}
                                    <div className="grid grid-cols-2 gap-3 mt-4">
                                        <button onClick={() => handleAction('Download Exam Report (PDF)')} className="p-3 rounded-lg border border-brand-500/30 bg-brand-500/10 hover:bg-brand-500/20 text-brand-400 text-sm font-semibold transition flex items-center justify-center gap-2">
                                            📄 Download Report
                                        </button>
                                        <button onClick={() => handleAction('Send Warning')} className="p-3 rounded-lg border border-amber-500/30 bg-amber-500/10 hover:bg-amber-500/20 text-amber-500 text-sm font-semibold transition flex items-center justify-center gap-2">
                                            ⚠️ Send Warning
                                        </button>
                                        <button onClick={() => handleAction('Lock Student')} className="col-span-2 p-3 rounded-lg border border-red-500/30 bg-red-500/10 hover:bg-red-500/20 text-red-500 text-sm font-semibold transition flex items-center justify-center gap-2">
                                            🛡️ Lock Student & Freeze Exam
                                        </button>
                                    </div>
                                </div>

                                {/* Snapshot Evidence System Log */}
                                <div className="bg-[#080808] rounded-xl border border-white/5 flex-1 flex flex-col shadow-xl overflow-hidden min-h-[250px]">
                                    <div className="p-4 border-b border-white/5 bg-white/[0.01]">
                                        <h3 className="text-sm font-semibold text-slate-300 uppercase tracking-wide flex items-center gap-2">
                                            📸 Snapshot Evidence Logs
                                        </h3>
                                    </div>
                                    <div className="flex-1 overflow-y-auto p-4 custom-scrollbar">
                                        {currentSelected.events.length > 0 ? (
                                            <div className="space-y-3">
                                                {currentSelected.events.map((ev, idx) => (
                                                    <div key={idx} className="bg-[#020202] p-3 rounded-lg border border-white/5 flex items-start gap-3 relative overflow-hidden group">
                                                        <div className="w-10 h-8 rounded bg-slate-800 flex items-center justify-center border border-white/10 shrink-0 group-hover:bg-slate-700 transition">
                                                            🖼️
                                                        </div>
                                                        <div className="flex flex-col flex-1 truncate">
                                                            <span className="text-sm text-slate-200 truncate pr-16">{ev.type}</span>
                                                            <span className="text-xs text-slate-500 font-mono mt-1">{ev.time} • Event #{ev.id}</span>
                                                        </div>
                                                        <span className="text-[10px] text-red-400 font-semibold bg-red-400/10 px-2 py-1 rounded absolute top-3 right-3 whitespace-nowrap">
                                                            Flagged
                                                        </span>
                                                    </div>
                                                ))}
                                            </div>
                                        ) : (
                                            <div className="h-full flex flex-col justify-center items-center text-slate-500 opacity-60 m-auto text-sm text-center">
                                                <span className="text-3xl mb-2">✅</span>
                                                <p>Clean Behavioral Record<br />No snapshots triggered.</p>
                                            </div>
                                        )}
                                    </div>
                                </div>
                            </div>
                        )
                    })() : (
                        <div className="bg-[#080808] rounded-xl border border-white/5 p-8 flex flex-col items-center justify-center text-center shadow-xl h-full opacity-60">
                            <span className="text-4xl mb-4">🎯</span>
                            <h3 className="text-lg font-semibold text-slate-300 mb-2">Proctor Intelligence Focus Mode</h3>
                            <p className="text-sm text-slate-500 max-w-sm">
                                Select a student from the active monitoring panel to view real-time behavioral diagnostics, snapshot evidence, and issue authoritative commands.
                            </p>
                        </div>
                    )}
                </div>
            </div>

            <style dangerouslySetInnerHTML={{
                __html: `
                .custom-scrollbar::-webkit-scrollbar { width: 6px; }
                .custom-scrollbar::-webkit-scrollbar-track { background: transparent; }
                .custom-scrollbar::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.1); border-radius: 4px; }
                .custom-scrollbar::-webkit-scrollbar-thumb:hover { background: rgba(255,255,255,0.2); }
            `}} />
        </div>
    )
}
