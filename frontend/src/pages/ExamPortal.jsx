/* eslint-disable react-hooks/set-state-in-effect */
import { useState, useCallback, useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import useMediaCapture from '../hooks/useMediaCapture'
import useKeystrokeTracker from '../hooks/useKeystrokeTracker'
import useMouseTracker from '../hooks/useMouseTracker'
import useExamWebSocket from '../hooks/useExamWebSocket'
import useExtensionDetector from '../hooks/useExtensionDetector'

const VideoStream = ({ stream, className }) => {
    const videoRef = useRef(null)
    useEffect(() => {
        if (videoRef.current && stream) {
            videoRef.current.srcObject = stream
        }
    }, [stream])
    return <video ref={videoRef} className={className} autoPlay muted playsInline />
}

// ─── Exam Data ──────────────────────────────────────────────────
const EXAM_SECTIONS = [
    {
        id: 'codealpha',
        title: 'CODEALPHA',
        subtitle: 'Multiple Choice',
        questions: [
            {
                id: 'q1', type: 'mcq', marks: 10,
                text: 'Which of the following is NOT a fundamental principle of Object-Oriented Programming?',
                options: ['Encapsulation', 'Polymorphism', 'Compilation', 'Inheritance']
            },
            {
                id: 'q2', type: 'mcq', marks: 10,
                text: 'What is the time complexity of searching for an element in a balanced Binary Search Tree?',
                options: ['O(1)', 'O(n)', 'O(log n)', 'O(n^2)']
            },
            {
                id: 'q3', type: 'mcq', marks: 10,
                text: 'Which data structure uses LIFO (Last In First Out) ordering?',
                options: ['Queue', 'Stack', 'Array', 'Hash Map']
            }
        ]
    },
    {
        id: 'logical',
        title: 'LOGICAL REASONING',
        subtitle: 'Paragraph',
        questions: [
            {
                id: 'q4', type: 'paragraph', marks: 15,
                text: 'Describe the OSI model and explain the function of each layer. How does data flow through these layers?'
            },
            {
                id: 'q5', type: 'paragraph', marks: 15,
                text: 'What is normalization in databases? Explain 1NF, 2NF, and 3NF with examples.'
            }
        ]
    },
    {
        id: 'codex',
        title: 'CODEX',
        subtitle: 'Programming',
        questions: [
            {
                id: 'q6', type: 'coding', marks: 20,
                text: 'Write a Python function `is_palindrome(s)` that checks if a given string is a valid palindrome, ignoring spaces, case, and punctuation.'
            }
        ]
    }
]

const ALL_QUESTIONS = EXAM_SECTIONS.flatMap(s => s.questions)
const TOTAL_MARKS = ALL_QUESTIONS.reduce((a, q) => a + q.marks, 0)

// ─── Component ──────────────────────────────────────────────────
export default function ExamPortal() {
    const navigate = useNavigate()
    const [sessionId] = useState(() => `exam-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`)
    const [phase, setPhase] = useState('setup') // setup | calibrating | exam | review | submitted
    const [currentSectionIdx, setCurrentSectionIdx] = useState(0)
    const [currentQIdx, setCurrentQIdx] = useState(0)
    const [answers, setAnswers] = useState({})
    const [markedForReview, setMarkedForReview] = useState({})
    const [examTime, setExamTime] = useState(3600)
    const [calibrationProgress, setCalibrationProgress] = useState(0)
    const [showSubmitConfirm, setShowSubmitConfirm] = useState(false)

    // Integrity tracking
    const [integrityScore, setIntegrityScore] = useState(100)
    const [, setWarnings] = useState(0)
    const [warningMsg, setWarningMsg] = useState(null)
    const [proctorMsgs, setProctorMsgs] = useState([{
        sender: 'System',
        text: 'Monitoring initialized.',
        time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    }])
    const [networkStable, setNetworkStable] = useState(true)
    const [lockdownCountdown, setLockdownCountdown] = useState(0)

    const timerRef = useRef(null)

    // Hooks
    const ws = useExamWebSocket({ sessionId })
    useExtensionDetector()
    const { sendFrame, sendAudio, sendKeystrokes, sendMouseData, sendText } = ws

    const media = useMediaCapture({
        onFrame: useCallback((frame) => sendFrame(frame), [sendFrame]),
        onAudioChunk: useCallback((audio) => sendAudio(audio), [sendAudio]),
        frameIntervalMs: 500,
        audioIntervalMs: 2000
    })

    const keyTracker = useKeystrokeTracker({
        onBatch: useCallback((batch) => sendKeystrokes(batch), [sendKeystrokes]),
        batchIntervalMs: 2000
    })

    const mouseTracker = useMouseTracker({
        onBatch: useCallback((batch) => sendMouseData(batch), [sendMouseData]),
        batchIntervalMs: 2000
    })

    // ─── Effects ────────────────────────────────────────────────
    useEffect(() => {
        if (phase !== 'exam') return
        const interval = setInterval(() => setNetworkStable(Math.random() > 0.05), 10000)
        return () => clearInterval(interval)
    }, [phase])

    useEffect(() => {
        if (ws.riskData && ws.riskData.overall_score !== undefined) {
            setIntegrityScore(Math.max(0, Math.round(100 - ws.riskData.overall_score)))
        }
    }, [ws.riskData])

    // Lockdown penalty countdown
    useEffect(() => {
        if (lockdownCountdown > 0) {
            const lktimer = setTimeout(() => setLockdownCountdown(prev => prev - 1), 1000)
            return () => clearTimeout(lktimer)
        }
    }, [lockdownCountdown])

    // Lockdown Event Listeners
    useEffect(() => {
        if (phase !== 'exam' && phase !== 'calibrating' && phase !== 'review') return
        const preventAction = (e) => e.preventDefault()
        document.addEventListener('contextmenu', preventAction)
        document.addEventListener('copy', preventAction)
        document.addEventListener('cut', preventAction)
        document.addEventListener('paste', preventAction)
        const handleKeyDown = (e) => {
            if (e.ctrlKey || e.metaKey || e.altKey) {
                if (['p', 's', 'u', 'i', 'c', 'v', 'x', 'a', 'tab'].includes(e.key.toLowerCase())) {
                    e.preventDefault()
                }
            }
        }
        document.addEventListener('keydown', handleKeyDown)
        return () => {
            document.removeEventListener('contextmenu', preventAction)
            document.removeEventListener('copy', preventAction)
            document.removeEventListener('cut', preventAction)
            document.removeEventListener('paste', preventAction)
            document.removeEventListener('keydown', handleKeyDown)
        }
    }, [phase])

    // Tab switch / blur detection
    useEffect(() => {
        if (phase !== 'exam' && phase !== 'review') return
        const triggerWarning = (reason) => {
            if (lockdownCountdown > 0) return // Debounce while already penalized

            // 1. Speak out loud
            if ('speechSynthesis' in window) {
                const utterance = new SpeechSynthesisUtterance(`Warning. Suspicious activity detected. ${reason}. Please focus on your screen immediately.`)
                utterance.rate = 1.05
                utterance.pitch = 0.9
                window.speechSynthesis.speak(utterance)
            }

            // 2. Lock screen for 5 seconds
            setLockdownCountdown(5)

            setWarnings(prev => {
                const newCount = prev + 1
                setProctorMsgs(m => [...m, { sender: 'System', text: `⚠ Anomaly: ${reason}`, time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) }])
                setIntegrityScore(s => Math.max(0, s - 10))
                return newCount
            })
        }
        const onFullscreenChange = () => { if (!document.fullscreenElement) triggerWarning("Exited full-screen mode") }
        const onVisibilityChange = () => { if (document.hidden) triggerWarning("Tab switched or minimized") }
        const onWindowBlur = () => { if (!warningMsg) triggerWarning("Clicked outside exam window") }
        document.addEventListener('fullscreenchange', onFullscreenChange)
        document.addEventListener('visibilitychange', onVisibilityChange)
        window.addEventListener('blur', onWindowBlur)
        return () => {
            document.removeEventListener('fullscreenchange', onFullscreenChange)
            document.removeEventListener('visibilitychange', onVisibilityChange)
            window.removeEventListener('blur', onWindowBlur)
        }
    }, [phase, warningMsg])

    // Final submit (irreversible)
    const finalSubmit = useCallback(() => {
        setShowSubmitConfirm(false)
        setPhase('submitted')
        media.stop()
        keyTracker.stop()
        mouseTracker.stop()
        ws.disconnect()
        if (timerRef.current) clearInterval(timerRef.current)
        if (document.fullscreenElement) document.exitFullscreen().catch(() => { })
    }, [media, keyTracker, mouseTracker, ws])

    const finalSubmitRef = useRef(finalSubmit)
    useEffect(() => { finalSubmitRef.current = finalSubmit }, [finalSubmit])

    // Timer
    useEffect(() => {
        if (phase === 'exam' || phase === 'review') {
            timerRef.current = setInterval(() => {
                setExamTime(prev => {
                    if (prev <= 0) { finalSubmitRef.current(); return 0 }
                    return prev - 1
                })
            }, 1000)
        }
        return () => { if (timerRef.current) clearInterval(timerRef.current) }
    }, [phase])

    // ─── Handlers ───────────────────────────────────────────────
    const handleAcknowledgeWarning = async () => {
        setWarningMsg(null)
        try { if (!document.fullscreenElement) await document.documentElement.requestFullscreen() }
        catch (e) { console.warn('Fullscreen error:', e) }
    }

    const requestProctorHelp = () => {
        setProctorMsgs(m => [...m, { sender: 'You', text: 'Requested help from proctor...', time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) }])
        setTimeout(() => {
            setProctorMsgs(m => [...m, { sender: 'Proctor (AI)', text: 'Session reviewed. Please continue.', time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) }])
        }, 3000)
    }

    const formatTimer = (secs) => {
        const h = Math.floor(secs / 3600)
        const m = Math.floor((secs % 3600) / 60)
        const s = secs % 60
        return `${h.toString().padStart(2, '0')}:${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`
    }

    const handleStartExam = async () => {
        try { await document.documentElement.requestFullscreen() }
        catch (e) { console.warn('Fullscreen error:', e) }
        setPhase('calibrating')
        await media.start()
        ws.connect()
        let progress = 0
        const cal = setInterval(() => {
            progress += 5
            setCalibrationProgress(progress)
            if (progress >= 100) {
                clearInterval(cal)
                setPhase('exam')
                keyTracker.start()
                mouseTracker.start()
            }
        }, 150)
    }

    const handleAnswerChange = (qId, val, isText = true) => {
        setAnswers(prev => ({ ...prev, [qId]: val }))
        if (isText && typeof val === 'string' && val.length > 50 && val.length % 20 === 0) sendText(val)
    }

    const toggleReview = (qId) => {
        setMarkedForReview(prev => ({ ...prev, [qId]: !prev[qId] }))
    }

    // Submit button → show confirmation
    const handleSubmitClick = () => setShowSubmitConfirm(true)

    // Go to review screen
    const handleGoToReview = () => { setShowSubmitConfirm(false); setPhase('review') }



    // ─── Derived ────────────────────────────────────────────────
    const getIntegrityStatus = () => {
        if (integrityScore >= 80) return { text: 'Stable', color: 'text-emerald-500', bg: 'bg-emerald-500/10', border: 'border-emerald-500/20', icon: '🟢' }
        if (integrityScore >= 50) return { text: 'Warning: Look at screen', color: 'text-amber-500', bg: 'bg-amber-500/10', border: 'border-amber-500/20', icon: '🟡' }
        return { text: 'Suspicious Activity Detected', color: 'text-red-500', bg: 'bg-red-500/10', border: 'border-red-500/20', icon: '🔴' }
    }
    const intStatus = getIntegrityStatus()

    const answeredCount = ALL_QUESTIONS.filter(q => answers[q.id]).length
    const reviewCount = ALL_QUESTIONS.filter(q => markedForReview[q.id]).length
    const unansweredCount = ALL_QUESTIONS.length - answeredCount

    // Question status helper
    const getQuestionStatus = (qId) => {
        if (markedForReview[qId]) return 'review'
        if (answers[qId]) return 'answered'
        return 'unanswered'
    }

    const statusColors = {
        answered: 'bg-emerald-600 text-white border-emerald-500/50',
        review: 'bg-amber-600 text-white border-amber-500/50',
        unanswered: 'bg-[#080808] text-slate-400 border-white/10 hover:border-white/20'
    }

    // AI module status from real WS data
    const getAiStatus = () => {
        const rd = ws.riskData
        const hasTracking = rd?.active_tracking
        return {
            face: hasTracking?.face_box ? 'Tracking' : (media.isActive ? 'Scanning...' : 'Offline'),
            gaze: hasTracking?.face_box ? 'Active' : (media.isActive ? 'Calibrating' : 'Offline'),
            audio: media.isActive ? 'Analyzing' : 'Offline',
            typing: rd?.stats?.keystrokes > 0 ? `${rd.stats.keystrokes} keys` : (phase === 'exam' ? 'Recording' : 'Idle'),
            tab: rd?.stats?.tab_switches > 0 ? `${rd.stats.tab_switches} switches` : 'Clean',
            objects: hasTracking?.objects?.filter(o => o.label !== 'Student Face').map(o => o.label).join(', ') || 'Clean',
        }
    }
    const aiStatus = getAiStatus()

    const aiColor = (val) => {
        if (val === 'Offline' || val === 'Idle') return 'text-red-400'
        if (val.includes('switch')) return 'text-amber-400'
        if (val !== 'Clean' && !['Tracking', 'Active', 'Analyzing', 'Recording'].includes(val) && !val.includes('keys')) return 'text-red-500 font-bold animate-pulse'
        return 'text-emerald-500'
    }

    // ═══════════════════════════════════════════════════════════
    // RENDER: Setup
    // ═══════════════════════════════════════════════════════════
    if (phase === 'setup') {
        const studentInfo = {
            name: 'Pradnyesh K.', id: '24BAI70609', course: 'B.Tech CSE (AI & ML)',
            exam: 'Behavioral AI Midterm', duration: '60 Minutes', attempt: '1 of 1',
            time: new Date().toLocaleDateString() + ' ' + new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
        }

        return (
            <div className="min-h-screen bg-[#020202] text-slate-200 font-sans flex items-center justify-center p-6 animate-fade-in relative overflow-hidden">
                <div className="absolute top-0 right-0 w-[500px] h-[500px] bg-brand-600/10 blur-[100px] rounded-full pointer-events-none" />
                <div className="bg-[#080808] border border-white/10 rounded-2xl p-8 max-w-2xl w-full shadow-2xl animate-scale-up relative z-10">
                    <div className="flex items-center justify-center gap-3 mb-6">
                        <div className="w-12 h-12 bg-gradient-to-br from-brand-500 to-emerald-400 rounded-xl flex items-center justify-center text-xl font-bold shadow-lg shadow-brand-500/20">T</div>
                        <h1 className="text-3xl font-bold text-white">Student Integrity Workspace</h1>
                    </div>
                    <p className="text-slate-400 text-center mb-8 text-sm leading-relaxed px-4">
                        The Student Workspace provides an overview of active and scheduled examinations, along with personalized AI integrity tracking.
                    </p>
                    <div className="bg-[#020202] rounded-xl border border-white/5 p-6 mb-8">
                        <h2 className="text-sm font-semibold text-slate-300 uppercase tracking-widest mb-4 border-b border-white/5 pb-2">Smart Exam Overview</h2>
                        <div className="grid grid-cols-2 gap-y-4 gap-x-8 text-sm">
                            {Object.entries({ 'Student Name': studentInfo.name, 'Student ID': studentInfo.id, 'Course': studentInfo.course, 'Exam': studentInfo.exam, 'Duration': studentInfo.duration, 'Attempt': studentInfo.attempt }).map(([k, v]) => (
                                <div key={k} className="flex flex-col">
                                    <span className="text-slate-500 uppercase text-xs mb-1">{k}</span>
                                    <span className={k === 'Student ID' ? 'font-mono text-brand-400 font-semibold' : 'font-semibold'}>{v}</span>
                                </div>
                            ))}
                            <div className="flex flex-col col-span-2">
                                <span className="text-slate-500 uppercase text-xs mb-1">Scheduled Time</span>
                                <span>{studentInfo.time}</span>
                            </div>
                        </div>
                    </div>
                    <div className="bg-[#020202] rounded-xl border border-brand-500/10 p-4 mb-8 text-xs text-slate-400">
                        <p className="font-semibold text-brand-400 mb-2">📋 Exam Structure</p>
                        {EXAM_SECTIONS.map(s => (
                            <div key={s.id} className="flex justify-between py-1 border-b border-white/5 last:border-0">
                                <span>{s.title} ({s.subtitle})</span>
                                <span className="text-slate-500">{s.questions.length} Q · {s.questions.reduce((a, q) => a + q.marks, 0)} pts</span>
                            </div>
                        ))}
                        <div className="flex justify-between pt-2 font-semibold text-slate-300">
                            <span>Total</span>
                            <span>{ALL_QUESTIONS.length} Questions · {TOTAL_MARKS} Points</span>
                        </div>
                    </div>
                    <div className="flex flex-col items-center">
                        <button className="bg-gradient-to-r from-brand-600 to-emerald-500 hover:from-brand-500 hover:to-emerald-400 text-white font-bold py-3.5 px-8 rounded-lg shadow-lg shadow-brand-600/20 hover:shadow-brand-600/40 transition-all flex items-center justify-center gap-2 text-sm uppercase tracking-wide w-full sm:w-auto" onClick={handleStartExam}>
                            <span>🔒</span> Enter Secure Environment
                        </button>
                        <button className="text-slate-500 hover:text-white transition mt-4 text-sm" onClick={() => navigate('/')}>Cancel and Return Home</button>
                    </div>
                </div>
            </div>
        )
    }

    // ═══════════════════════════════════════════════════════════
    // RENDER: Calibrating
    // ═══════════════════════════════════════════════════════════
    if (phase === 'calibrating') {
        return (
            <div className="min-h-screen bg-[#020202] text-white flex flex-col items-center justify-center p-6 animate-fade-in text-center">
                <h2 className="text-3xl font-bold mb-4 font-mono">Initializing AI Models...</h2>
                <p className="text-slate-400 mb-8 max-w-md">Calibrating Head Pose, Eye Gaze, and Emotion Detection Baseline. Please sit naturally.</p>
                <div className="relative w-72 h-72 rounded-full overflow-hidden border-4 border-brand-500/30 mb-8 shadow-[0_0_50px_rgba(59,130,246,0.2)]">
                    <VideoStream stream={media.stream} className="w-full h-full object-cover scale-110" />
                    <div className="absolute inset-0 border-4 border-brand-500 rounded-full animate-[spin_3s_linear_infinite] border-t-transparent border-b-transparent" />
                    <div className="absolute inset-0 bg-brand-500/10" />
                </div>
                <div className="w-64 bg-[#080808] rounded-full h-2 mb-2 overflow-hidden">
                    <div className="bg-gradient-to-r from-emerald-400 to-brand-500 h-full transition-all duration-150" style={{ width: `${calibrationProgress}%` }} />
                </div>
                <span className="text-brand-400 font-mono text-sm">{calibrationProgress}%</span>
            </div>
        )
    }

    // ═══════════════════════════════════════════════════════════
    // RENDER: Review Screen
    // ═══════════════════════════════════════════════════════════
    if (phase === 'review') {
        return (
            <div className="min-h-screen bg-[#020202] text-slate-200 font-sans p-6 md:p-12 animate-fade-in">
                {/* Warning overlay still active */}
                {warningMsg && (
                    <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
                        <div className="bg-[#050202] border border-red-500/50 rounded-2xl p-8 max-w-lg w-full shadow-[0_0_100px_rgba(239,68,68,0.2)] text-center">
                            <div className="text-6xl mb-4">⚠️</div>
                            <h2 className="text-2xl font-bold text-red-500 mb-4">Suspicious Activity Detected</h2>
                            <p className="text-slate-300 mb-8">{warningMsg}</p>
                            <button onClick={handleAcknowledgeWarning} className="w-full bg-red-600 hover:bg-red-700 text-white font-bold py-3 px-6 rounded-lg">Acknowledge & Continue</button>
                        </div>
                    </div>
                )}

                <div className="max-w-4xl mx-auto">
                    {/* Header */}
                    <div className="flex items-center justify-between mb-8">
                        <div>
                            <h1 className="text-2xl font-bold text-white mb-1">Review Your Answers</h1>
                            <p className="text-slate-400 text-sm">Review all questions before final submission. Once submitted, you cannot return.</p>
                        </div>
                        <div className={`px-4 py-1.5 rounded-md font-mono text-lg font-bold border ${examTime < 300 ? 'bg-red-500/10 text-red-500 border-red-500/30 animate-pulse' : 'bg-white/5 text-white border-white/10'}`}>
                            {formatTimer(examTime)}
                        </div>
                    </div>

                    {/* Summary Stats */}
                    <div className="grid grid-cols-3 gap-4 mb-8">
                        <div className="bg-emerald-500/10 border border-emerald-500/20 rounded-xl p-4 text-center">
                            <div className="text-3xl font-bold text-emerald-400">{answeredCount}</div>
                            <div className="text-xs text-emerald-500/70 uppercase tracking-wider mt-1">Answered</div>
                        </div>
                        <div className="bg-amber-500/10 border border-amber-500/20 rounded-xl p-4 text-center">
                            <div className="text-3xl font-bold text-amber-400">{reviewCount}</div>
                            <div className="text-xs text-amber-500/70 uppercase tracking-wider mt-1">Marked for Review</div>
                        </div>
                        <div className="bg-red-500/10 border border-red-500/20 rounded-xl p-4 text-center">
                            <div className="text-3xl font-bold text-red-400">{unansweredCount}</div>
                            <div className="text-xs text-red-500/70 uppercase tracking-wider mt-1">Unanswered</div>
                        </div>
                    </div>

                    {/* Section-wise question list */}
                    {EXAM_SECTIONS.map((sec, si) => (
                        <div key={sec.id} className="mb-6">
                            <h3 className="text-sm font-semibold text-slate-500 uppercase tracking-widest mb-3">{sec.title} — {sec.subtitle}</h3>
                            <div className="space-y-2">
                                {sec.questions.map((q, qi) => {
                                    const status = getQuestionStatus(q.id)
                                    return (
                                        <div key={q.id} className="bg-[#080808] border border-white/5 rounded-lg p-4 flex items-center justify-between gap-4">
                                            <div className="flex items-center gap-3 flex-1 min-w-0">
                                                <span className={`w-8 h-8 rounded text-sm font-bold flex items-center justify-center shrink-0 ${statusColors[status]}`}>
                                                    {qi + 1}
                                                </span>
                                                <p className="text-sm text-slate-300 truncate">{q.text}</p>
                                            </div>
                                            <div className="flex items-center gap-2 shrink-0">
                                                <span className="text-xs text-slate-500">{q.marks} pts</span>
                                                {status === 'answered' && <span className="text-xs bg-emerald-500/20 text-emerald-400 px-2 py-0.5 rounded">✓ Answered</span>}
                                                {status === 'review' && <span className="text-xs bg-amber-500/20 text-amber-400 px-2 py-0.5 rounded">🔖 Review</span>}
                                                {status === 'unanswered' && <span className="text-xs bg-red-500/20 text-red-400 px-2 py-0.5 rounded">✗ Unanswered</span>}
                                                <button
                                                    onClick={() => { setCurrentSectionIdx(si); setCurrentQIdx(qi); setPhase('exam') }}
                                                    className="text-xs bg-brand-500/20 text-brand-400 px-3 py-1 rounded hover:bg-brand-500/30 transition"
                                                >
                                                    Edit
                                                </button>
                                            </div>
                                        </div>
                                    )
                                })}
                            </div>
                        </div>
                    ))}

                    {/* Action Buttons */}
                    <div className="flex items-center justify-between mt-8 pt-6 border-t border-white/5">
                        <button onClick={() => setPhase('exam')} className="bg-[#080808] hover:bg-[#1a2332] text-slate-300 font-medium py-3 px-6 rounded-lg transition border border-white/10">
                            ← Back to Exam
                        </button>
                        <button onClick={finalSubmit} className="bg-gradient-to-r from-red-600 to-red-700 hover:from-red-500 hover:to-red-600 text-white font-bold py-3 px-8 rounded-lg shadow-lg shadow-red-600/20 transition-all">
                            🔒 Final Submit ({answeredCount}/{ALL_QUESTIONS.length} answered)
                        </button>
                    </div>
                </div>
            </div>
        )
    }

    // ═══════════════════════════════════════════════════════════
    // RENDER: Submitted
    // ═══════════════════════════════════════════════════════════
    if (phase === 'submitted') {
        return (
            <div className="min-h-screen bg-[#020202] text-slate-200 font-sans p-6 md:p-12 animate-fade-in flex flex-col items-center justify-center">
                <div className="bg-[#080808] border border-white/5 rounded-2xl p-8 max-w-3xl w-full shadow-2xl animate-slide-up">
                    <div className="flex flex-col items-center text-center mb-10 border-b border-white/5 pb-8">
                        <div className="w-20 h-20 bg-emerald-500/10 border border-emerald-500/30 rounded-full flex items-center justify-center text-emerald-400 mb-4 shadow-[0_0_30px_rgba(16,185,129,0.2)]">
                            <svg className="w-10 h-10" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={3}>
                                <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                            </svg>
                        </div>
                        <h1 className="text-3xl font-bold text-white mb-2">Exam Successfully Submitted</h1>
                        <p className="text-slate-400 max-w-lg">Your answers have been securely recorded. The AI behavioral integrity report is attached.</p>
                    </div>
                    <h2 className="text-sm font-semibold text-slate-500 uppercase tracking-widest mb-4">Exam Summary</h2>
                    <div className="overflow-x-auto rounded-lg border border-white/5 mb-8">
                        <table className="w-full text-sm text-left">
                            <thead className="bg-[#020202] text-slate-400 uppercase text-xs">
                                <tr>
                                    <th className="px-6 py-4 font-semibold">Exam</th>
                                    <th className="px-6 py-4 font-semibold">Date</th>
                                    <th className="px-6 py-4 font-semibold">Answered</th>
                                    <th className="px-6 py-4 font-semibold">Integrity</th>
                                </tr>
                            </thead>
                            <tbody>
                                <tr className="bg-white/[0.01]">
                                    <td className="px-6 py-4 font-medium text-white">Behavioral AI Midterm</td>
                                    <td className="px-6 py-4 text-slate-400">{new Date().toLocaleDateString()}</td>
                                    <td className="px-6 py-4 text-brand-400 font-mono">{answeredCount}/{ALL_QUESTIONS.length}</td>
                                    <td className="px-6 py-4">
                                        <div className="flex items-center gap-2">
                                            <span className={`font-mono font-bold ${intStatus.color}`}>{integrityScore}%</span>
                                            <span className="text-xs text-slate-500 border border-white/10 px-2 py-0.5 rounded uppercase tracking-wider">AI Verified</span>
                                        </div>
                                    </td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                    <div className="flex justify-center">
                        <button className="bg-slate-800 hover:bg-slate-700 text-white font-medium py-2.5 px-6 rounded-lg transition-colors border border-white/10" onClick={() => navigate('/')}>
                            Return to Organization Home
                        </button>
                    </div>
                </div>
            </div>
        )
    }

    // ═══════════════════════════════════════════════════════════
    // RENDER: Active Exam
    // ═══════════════════════════════════════════════════════════
    const section = EXAM_SECTIONS[currentSectionIdx]
    const question = section?.questions?.[currentQIdx]

    if (!section || !question) {
        return null
    }



    return (
        <div className="min-h-screen bg-[#020202] text-slate-200 font-sans flex flex-col overflow-hidden relative">

            {/* Impassable Proctor Lockdown Modal */}
            {lockdownCountdown > 0 && (
                <div className="fixed inset-0 z-[9999] bg-black/95 backdrop-blur-md flex items-center justify-center p-4">
                    <div className="bg-red-500/10 border border-red-500/40 rounded-2xl p-8 max-w-lg w-full shadow-[0_0_50px_rgba(239,68,68,0.3)] text-center animate-pulse">
                        <div className="w-20 h-20 bg-red-500/20 border border-red-500/50 rounded-full flex items-center justify-center text-4xl mb-6 mx-auto">
                            🛡️
                        </div>
                        <h2 className="text-3xl font-bold text-red-500 mb-2 uppercase tracking-widest">Proctor Lockdown</h2>
                        <p className="text-red-200/80 mb-8 font-mono text-sm leading-relaxed">
                            Suspicious activity intercepted.<br/>The exam has been temporarily suspended.
                        </p>
                        <div className="text-7xl font-mono font-bold text-red-400 mb-8 drop-shadow-[0_0_15px_rgba(239,68,68,0.8)]">
                            0{lockdownCountdown}
                        </div>
                        <div className="text-xs text-red-500/60 uppercase tracking-widest">
                            Return to the exam and face the camera.
                        </div>
                    </div>
                </div>
            )}

            {/* Submit Confirmation Modal */}
            {showSubmitConfirm && (
                <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4 animate-fade-in">
                    <div className="bg-[#080808] border border-white/10 rounded-2xl p-8 max-w-md w-full shadow-2xl text-center">
                        <div className="text-5xl mb-4">📝</div>
                        <h2 className="text-xl font-bold text-white mb-2">Submit Exam?</h2>
                        <p className="text-slate-400 text-sm mb-6">
                            You have answered <span className="text-emerald-400 font-bold">{answeredCount}</span> of <span className="text-white font-bold">{ALL_QUESTIONS.length}</span> questions.
                            {unansweredCount > 0 && <span className="text-amber-400"> ({unansweredCount} unanswered)</span>}
                            {reviewCount > 0 && <span className="text-amber-400"> ({reviewCount} marked for review)</span>}
                        </p>
                        <div className="space-y-3">
                            <button onClick={handleGoToReview} className="w-full bg-brand-600 hover:bg-blue-700 text-white font-semibold py-3 px-6 rounded-lg transition-colors">
                                📋 Review Answers First
                            </button>
                            <button onClick={finalSubmit} className="w-full bg-red-600 hover:bg-red-700 text-white font-semibold py-3 px-6 rounded-lg transition-colors">
                                🔒 Submit Now (No Going Back)
                            </button>
                            <button onClick={() => setShowSubmitConfirm(false)} className="w-full bg-[#020202] hover:bg-[#1a2332] text-slate-400 font-medium py-3 px-6 rounded-lg transition-colors border border-white/10">
                                Cancel
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {/* Warning Overlay */}
            {warningMsg && (
                <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4 animate-fade-in">
                    <div className="bg-[#050202] border border-red-500/50 rounded-2xl p-8 max-w-lg w-full shadow-[0_0_100px_rgba(239,68,68,0.2)] text-center animate-scale-up">
                        <div className="text-6xl mb-4">⚠️</div>
                        <h2 className="text-2xl font-bold text-red-500 mb-4">Suspicious Activity Detected</h2>
                        <p className="text-slate-300 mb-8">{warningMsg}</p>
                        <button onClick={handleAcknowledgeWarning} className="w-full bg-red-600 hover:bg-red-700 text-white font-bold py-3 px-6 rounded-lg transition-colors">
                            Acknowledge & Continue Exam
                        </button>
                    </div>
                </div>
            )}

            {/* Top Header */}
            <header className="h-16 border-b border-white/5 bg-[#080808] flex items-center justify-between px-6 shrink-0 z-10">
                <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded bg-gradient-to-br from-brand-500 to-emerald-400 flex items-center justify-center text-sm font-bold shadow-lg shadow-brand-500/20">T</div>
                    <span className="font-semibold text-white tracking-wide">TrustIQ Workspace</span>
                </div>
                <div className="flex items-center gap-6">
                    <div className="flex items-center gap-4 text-xs font-mono text-slate-400">
                        <div className="flex items-center gap-1.5"><span className={`w-2 h-2 rounded-full ${media.isActive ? 'bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.8)]' : 'bg-red-500'}`} /> Camera</div>
                        <div className="flex items-center gap-1.5"><span className={`w-2 h-2 rounded-full ${media.isActive ? 'bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.8)]' : 'bg-red-500'}`} /> Mic</div>
                        <div className="flex items-center gap-1.5"><span className={`w-2 h-2 rounded-full ${networkStable ? 'bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.8)]' : 'bg-amber-500'}`} /> Network</div>
                    </div>
                    <div className={`px-4 py-1.5 rounded-md font-mono text-lg font-bold border ${examTime < 300 ? 'bg-red-500/10 text-red-500 border-red-500/30 animate-pulse' : 'bg-white/5 text-white border-white/10'}`}>
                        {formatTimer(examTime)}
                    </div>
                    <button className="bg-red-500 hover:bg-red-600 text-white text-sm font-semibold px-4 py-1.5 rounded shadow shadow-red-500/20 transition-colors" onClick={handleSubmitClick}>
                        Submit
                    </button>
                </div>
            </header>

            <div className="flex flex-1 overflow-hidden">
                {/* LEFT SIDEBAR */}
                <div className="w-72 border-r border-white/5 bg-[#080808] flex flex-col p-5 overflow-y-auto custom-scrollbar shrink-0">

                    {/* Integrity */}
                    <div className={`mb-5 p-4 rounded-xl border ${intStatus.border} ${intStatus.bg}`}>
                        <div className="flex items-center gap-2 mb-1">
                            <span className="text-lg">{intStatus.icon}</span>
                            <span className={`text-sm font-semibold ${intStatus.color}`}>Integrity</span>
                        </div>
                        <div className={`text-xs font-medium ${intStatus.color}`}>{intStatus.text}</div>
                    </div>

                    {/* Score Bar */}
                    <div className="mb-6">
                        <div className="flex justify-between items-end mb-2">
                            <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Your Score</h3>
                            <span className={`font-mono font-bold text-lg ${intStatus.color}`}>{integrityScore}%</span>
                        </div>
                        <div className="w-full bg-[#020202] h-2.5 rounded-full overflow-hidden border border-white/5 relative">
                            <div className="h-full bg-gradient-to-r from-red-500 via-amber-500 to-emerald-500 w-full opacity-30 absolute" />
                            <div className="h-full bg-slate-800 transition-all duration-1000 ease-out absolute right-0" style={{ width: `${100 - integrityScore}%` }} />
                        </div>
                    </div>

                    {/* Webcam */}
                    <div className="mb-6 relative rounded-xl overflow-hidden border border-white/10 group">
                        <VideoStream stream={media.stream} className="w-full h-32 object-cover object-center" />
                        <div className="absolute top-2 left-2 bg-black/60 backdrop-blur text-[10px] font-mono px-2 py-0.5 rounded text-emerald-400 border border-emerald-500/20 flex items-center gap-1.5">
                            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
                            Live
                        </div>
                        {ws.riskData?.active_tracking?.objects?.length > 0 ? (
                            ws.riskData.active_tracking.objects.map((obj, i) => (
                                <div key={i} className={`absolute border-2 ${obj.color} rounded pointer-events-none transition-all duration-300 shadow-lg`} style={{
                                    left: `${obj.box.xmin * 100}%`,
                                    top: `${obj.box.ymin * 100}%`,
                                    width: `${obj.box.width * 100}%`,
                                    height: `${obj.box.height * 100}%`,
                                }}>
                                    <span className={`absolute -top-4 left-0 text-[8px] font-bold px-1 rounded-sm ${obj.bg} ${obj.color.split(' ')[0]} whitespace-nowrap`}>
                                        {obj.label}
                                    </span>
                                </div>
                            ))
                        ) : (
                            <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-16 h-20 border border-emerald-500/20 rounded-lg pointer-events-none border-dashed" />
                        )}
                    </div>

                    {/* Dynamic AI Panel */}
                    <div className="mb-6">
                        <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-3">AI Analysis Engine</h3>
                        <div className="space-y-1.5 text-xs font-mono">
                            {[
                                ['Face & Pose', aiStatus.face],
                                ['Eye Gaze', aiStatus.gaze],
                                ['Background Audio', aiStatus.audio],
                                ['Typing Rhythm', aiStatus.typing],
                                ['Tab Activity', aiStatus.tab],
                                ['Environment', aiStatus.objects],
                            ].map(([label, val]) => (
                                <div key={label} className="flex justify-between items-center bg-[#020202] p-2 rounded border border-white/5">
                                    <span className="text-slate-500">{label}</span>
                                    <span className={aiColor(val)}>{val}</span>
                                </div>
                            ))}
                        </div>
                    </div>

                    {/* Progress Summary */}
                    <div className="mb-6 bg-[#020202] rounded-lg border border-white/5 p-3">
                        <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">Progress</h3>
                        <div className="flex gap-3 text-center">
                            <div className="flex-1"><div className="text-lg font-bold text-emerald-400">{answeredCount}</div><div className="text-[10px] text-slate-500">Done</div></div>
                            <div className="flex-1"><div className="text-lg font-bold text-amber-400">{reviewCount}</div><div className="text-[10px] text-slate-500">Review</div></div>
                            <div className="flex-1"><div className="text-lg font-bold text-slate-400">{unansweredCount}</div><div className="text-[10px] text-slate-500">Left</div></div>
                        </div>
                    </div>

                    {/* Proctor Chat */}
                    <div className="border-t border-white/5 pt-4 mt-auto">
                        <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-3 flex items-center justify-between">
                            Proctor Chat
                            <button onClick={requestProctorHelp} className="text-[10px] bg-brand-500/20 text-brand-400 px-2 py-1 rounded hover:bg-brand-500/30 transition">Help</button>
                        </h3>
                        <div className="bg-[#020202] border border-white/5 rounded-lg p-3 h-32 overflow-y-auto custom-scrollbar flex flex-col gap-2">
                            {proctorMsgs.map((msg, i) => (
                                <div key={i} className={`text-xs ${msg.sender === 'You' ? 'text-right' : ''}`}>
                                    <span className={`block font-semibold mb-0.5 ${msg.sender === 'System' ? 'text-amber-500' : msg.sender === 'You' ? 'text-brand-400' : 'text-slate-300'}`}>{msg.sender}</span>
                                    <span className="text-slate-400 bg-white/5 inline-block p-1.5 rounded">{msg.text}</span>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>

                {/* CENTRAL EXAM AREA */}
                <div className="flex-1 flex flex-col bg-[#020202] relative">
                    {/* Section Tabs */}
                    <div className="flex border-b border-white/5 bg-white/[0.01] overflow-x-auto">
                        {EXAM_SECTIONS.map((sec, i) => (
                            <button key={sec.id} onClick={() => { setCurrentSectionIdx(i); setCurrentQIdx(0) }} className={`px-5 py-3.5 text-sm font-semibold border-b-2 transition-colors whitespace-nowrap ${i === currentSectionIdx ? 'border-brand-500 text-brand-400 bg-brand-500/5' : 'border-transparent text-slate-500 hover:text-slate-300'}`}>
                                {sec.title}
                                <span className="text-[10px] ml-1.5 opacity-60">({sec.subtitle})</span>
                            </button>
                        ))}
                    </div>

                    {/* Question Area */}
                    <div className="flex-1 flex flex-col max-w-4xl mx-auto w-full p-8 md:p-10 overflow-y-auto custom-scrollbar">
                        {/* Question nav */}
                        <div className="flex items-center gap-2 mb-5 flex-wrap">
                            {section.questions.map((q, i) => (
                                <button key={q.id} onClick={() => setCurrentQIdx(i)} className={`w-9 h-9 rounded text-sm font-semibold transition-all border ${i === currentQIdx ? 'ring-2 ring-brand-500 ring-offset-2 ring-offset-[#020202] ' : ''} ${statusColors[getQuestionStatus(q.id)]}`}>
                                    {i + 1}
                                </button>
                            ))}
                            <div className="ml-auto flex items-center gap-2 text-[10px] text-slate-500">
                                <span className="flex items-center gap-1"><span className="w-3 h-3 rounded bg-emerald-600 inline-block" /> Answered</span>
                                <span className="flex items-center gap-1"><span className="w-3 h-3 rounded bg-amber-600 inline-block" /> Review</span>
                                <span className="flex items-center gap-1"><span className="w-3 h-3 rounded bg-[#080808] border border-white/10 inline-block" /> Empty</span>
                            </div>
                        </div>

                        {/* Question header */}
                        <div className="flex items-center justify-between mb-4">
                            <span className="text-sm font-semibold text-brand-400 uppercase tracking-widest">Q{currentQIdx + 1}</span>
                            <div className="flex items-center gap-2">
                                <span className="text-sm font-semibold text-slate-500 bg-white/5 px-3 py-1 rounded">{question.marks} pts</span>
                                <button onClick={() => toggleReview(question.id)} className={`text-xs px-3 py-1 rounded transition-colors ${markedForReview[question.id] ? 'bg-amber-500/20 text-amber-400 border border-amber-500/30' : 'bg-white/5 text-slate-500 hover:text-amber-400 border border-white/10'}`}>
                                    {markedForReview[question.id] ? '🔖 Marked' : '🔖 Mark for Review'}
                                </button>
                            </div>
                        </div>

                        <p className="text-xl font-medium text-white mb-8 leading-relaxed">{question.text}</p>

                        {/* Answer Input */}
                        <div className="flex-1 relative flex flex-col">
                            {question.type === 'mcq' ? (
                                <div className="space-y-3">
                                    {question.options.map((opt, i) => (
                                        <label key={i} onClick={() => handleAnswerChange(question.id, opt, false)} className={`flex items-center gap-4 p-4 rounded-xl border cursor-pointer transition-all ${answers[question.id] === opt ? 'bg-brand-500/10 border-brand-500/50 text-brand-300 shadow-[0_0_20px_rgba(59,130,246,0.1)]' : 'bg-[#080808] border-white/10 text-slate-300 hover:border-white/30 hover:bg-white/[0.02]'}`}>
                                            <div className={`w-5 h-5 rounded-full border-2 flex items-center justify-center shrink-0 transition-colors ${answers[question.id] === opt ? 'border-brand-500 bg-brand-500' : 'border-slate-500'}`}>
                                                {answers[question.id] === opt && <div className="w-2 h-2 rounded-full bg-white" />}
                                            </div>
                                            <span className="text-base">{opt}</span>
                                        </label>
                                    ))}
                                </div>
                            ) : question.type === 'coding' ? (
                                <div className="flex-1 bg-[#080808] rounded-xl border border-white/10 overflow-hidden flex flex-col shadow-inner min-h-[350px]">
                                    <div className="h-10 bg-[#020202] border-b border-white/10 flex items-center px-4 gap-2">
                                        <span className="w-3 h-3 rounded-full bg-red-500/60" />
                                        <span className="w-3 h-3 rounded-full bg-amber-500/60" />
                                        <span className="w-3 h-3 rounded-full bg-emerald-500/60" />
                                        <span className="text-xs font-mono text-slate-400 ml-2">main.py</span>
                                    </div>
                                    <textarea
                                        className="w-full flex-1 bg-transparent p-6 text-emerald-400 font-mono text-sm leading-relaxed focus:outline-none resize-none"
                                        placeholder="# Write your code here..."
                                        value={answers[question.id] || ''}
                                        onChange={e => handleAnswerChange(question.id, e.target.value)}
                                        spellCheck={false}
                                    />
                                </div>
                            ) : (
                                <textarea
                                    className="w-full min-h-[300px] flex-1 bg-[#080808] border border-white/10 rounded-xl p-6 text-slate-200 text-lg leading-relaxed focus:outline-none focus:border-brand-500/50 resize-none transition-colors shadow-inner"
                                    placeholder="Type your answer here..."
                                    value={answers[question.id] || ''}
                                    onChange={e => handleAnswerChange(question.id, e.target.value)}
                                />
                            )}
                        </div>

                        {/* Navigation */}
                        <div className="flex items-center justify-between mt-6 pt-4 border-t border-white/5">
                            <button
                                disabled={currentSectionIdx === 0 && currentQIdx === 0}
                                onClick={() => {
                                    if (currentQIdx > 0) setCurrentQIdx(currentQIdx - 1)
                                    else if (currentSectionIdx > 0) {
                                        const prevSec = EXAM_SECTIONS[currentSectionIdx - 1]
                                        setCurrentSectionIdx(currentSectionIdx - 1)
                                        setCurrentQIdx(prevSec.questions.length - 1)
                                    }
                                }}
                                className="px-5 py-2 rounded-lg text-sm font-medium border border-white/10 text-slate-400 hover:text-white hover:bg-white/5 transition disabled:opacity-30 disabled:pointer-events-none"
                            >
                                ← Previous
                            </button>

                            <span className="text-xs text-slate-500 font-mono">
                                {currentQIdx + 1}/{section.questions.length} in {section.title}
                            </span>

                            {currentSectionIdx === EXAM_SECTIONS.length - 1 && currentQIdx === section.questions.length - 1 ? (
                                <button onClick={handleSubmitClick} className="px-5 py-2 rounded-lg text-sm font-semibold bg-red-600 hover:bg-red-700 text-white transition shadow shadow-red-500/20">
                                    Review & Submit →
                                </button>
                            ) : (
                                <button
                                    onClick={() => {
                                        if (currentQIdx < section.questions.length - 1) setCurrentQIdx(currentQIdx + 1)
                                        else if (currentSectionIdx < EXAM_SECTIONS.length - 1) {
                                            setCurrentSectionIdx(currentSectionIdx + 1)
                                            setCurrentQIdx(0)
                                        }
                                    }}
                                    className="px-5 py-2 rounded-lg text-sm font-medium bg-brand-600 hover:bg-blue-700 text-white transition"
                                >
                                    Next →
                                </button>
                            )}
                        </div>
                    </div>
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
