import { useNavigate } from 'react-router-dom'

const FEATURES = [
    {
        icon: '👁️',
        title: 'Visual Context Monitoring',
        desc: 'Smart gaze and face tracking that understands natural movements, ensuring integrity without feeling invasive.',
        color: 'from-brand-500 to-emerald-400'
    },
    {
        icon: '⌨️',
        title: 'Natural Typing Rhythms',
        desc: 'Verifies student identity seamlessly through their unique typing patterns, avoiding the need for strict device scans.',
        color: 'from-emerald-500 to-green-400'
    },
    {
        icon: '🎙️',
        title: 'Gentle Audio Analysis',
        desc: 'Filters out everyday household noises to flag only genuinely suspicious audio, respecting the student\'s environment.',
        color: 'from-brand-600 to-teal-400'
    },
    {
        icon: '✍️',
        title: 'Writing Style Analysis',
        desc: 'A quiet background check that compares exam answers to standard AI-generated text, keeping original thought rewarded.',
        color: 'from-green-500 to-emerald-400'
    },
    {
        icon: '🧠',
        title: 'Fair Evaluation Engine',
        desc: 'Combines every signal into a single, easy-to-understand confidence score so proctors can make fair, informed decisions.',
        color: 'from-brand-400 to-green-300'
    },
    {
        icon: '🔒',
        title: 'Distraction-Free Environment',
        desc: 'A gentle browser lockdown mode that prevents tab switching gracefully, helping students stay deeply focused.',
        color: 'from-green-600 to-emerald-500'
    }
]

const STEPS = [
    { num: '01', title: 'Set Up Seamlessly', desc: 'Teachers drop in their exam details and choose the proctoring sensitivity. Taking just two minutes.' },
    { num: '02', title: 'Students Check In', desc: 'Students join via a clean portal, grant necessary permissions, and calibrate effortlessly.' },
    { num: '03', title: 'Quiet Observation', desc: 'TrustIQ hums in the background, analyzing focus and behavior without popping up stressful warnings.' },
    { num: '04', title: 'Review Fairly', desc: 'Proctors get a clean, human-readable summary of the session to review flagged moments, not false alarms.' }
]

const PRICING = [
    {
        name: 'Starter',
        price: 'Free',
        period: '',
        desc: 'Perfect for giving TrustIQ a try.',
        features: ['Up to 30 students', '5 exams total', 'Visual AI only', 'Basic confidence score', 'Community support'],
        cta: 'Get Started',
        highlight: false
    },
    {
        name: 'Pro',
        price: '$4',
        period: '/student/exam',
        desc: 'For universities that care about fairness.',
        features: ['Unlimited students', 'Unlimited exams', 'All 4 Smart Modules', 'Detailed fair reports', 'Priority Email Support', '30-day data retention'],
        cta: 'Start Pro Trial',
        highlight: true
    },
    {
        name: 'Enterprise',
        price: 'Custom',
        period: '',
        desc: 'For institutions needing deep control.',
        features: ['Everything in Pro', 'Seamless SSO integration', 'Brand customisation', 'Dedicated success rep', '99.9% uptime SLA', 'API access'],
        cta: 'Contact Sales',
        highlight: false
    }
]

export default function Landing() {
    const navigate = useNavigate()

    return (
        <div className="min-h-screen bg-surface-dark text-white font-sans antialiased selection:bg-brand-500/30 selection:text-brand-200">

            {/* ─── Navbar ─── */}
            <nav className="fixed top-0 left-0 right-0 z-50 bg-[#020202]/80 backdrop-blur-xl border-b border-white/5 transition-all">
                <div className="max-w-7xl mx-auto px-6 h-20 flex items-center justify-between">
                    
                    {/* Logo */}
                    <div className="flex items-center gap-3 cursor-pointer" onClick={() => window.scrollTo(0, 0)}>
                        <div className="relative w-8 h-8 rounded-full border border-brand-500/30 bg-brand-500/10 flex items-center justify-center overflow-hidden">
                            <div className="w-4 h-4 bg-brand-400 rounded-full blur-[2px] shadow-[0_0_15px_rgba(5,208,104,0.8)]"></div>
                        </div>
                        <span className="text-xl font-medium tracking-tight">TrustIQ</span>
                    </div>

                    {/* Center Links */}
                    <div className="hidden md:flex items-center gap-8 text-sm text-slate-300 font-medium tracking-wide">
                        <a href="#features" className="hover:text-white transition">Features</a>
                        <a href="#how-it-works" className="hover:text-white transition">How It Works</a>
                        <a href="#pricing" className="hover:text-white transition">Pricing</a>
                        <a href="#" className="hover:text-white transition group flex items-center gap-1">
                            Use Cases
                            <svg className="w-3 h-3 text-slate-500 group-hover:text-slate-300 transition-colors" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" /></svg>
                        </a>
                    </div>

                    {/* Right CTA */}
                    <div className="flex items-center gap-4">
                        <button onClick={() => window.open('/login', '_blank')} className="hidden sm:block text-sm text-slate-300 hover:text-white transition font-medium">Log In</button>
                        <button 
                            onClick={() => window.open('/login', '_blank')} 
                            className="text-sm border border-brand-500/50 hover:bg-brand-500/10 text-brand-400 px-5 py-2 rounded-full font-medium transition flex items-center gap-2 group"
                        >
                            <svg className="w-4 h-4 opacity-70 group-hover:opacity-100 transition" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" /></svg>
                            Get TrustIQ
                        </button>
                    </div>
                </div>
            </nav>

            {/* ─── Hero Section ─── */}
            <section className="relative pt-40 pb-32 px-6 flex flex-col items-center justify-center min-h-[90vh] overflow-hidden">
                
                {/* Wavy/Mesh Background Effect */}
                <div className="absolute inset-0 z-0 pointer-events-none flex justify-center items-center opacity-40">
                    <div className="w-[800px] h-[400px] bg-brand-500/20 blur-[120px] rounded-[100%] absolute top-10 rotate-12"></div>
                    <div className="w-[600px] h-[300px] bg-emerald-700/20 blur-[100px] rounded-[100%] absolute bottom-20 -rotate-12"></div>
                </div>
                
                {/* Diagonal subtle lines overlay to mimic the wave pattern */}
                <div className="absolute inset-0 z-0 pointer-events-none opacity-[0.03]" style={{ backgroundImage: 'repeating-linear-gradient(45deg, #000 0, #000 2px, #fff 2px, #fff 4px)', backgroundSize: '100% 100%' }}></div>

                <div className="max-w-4xl mx-auto text-center relative z-10 flex flex-col items-center">
                    
                    {/* Badge */}
                    <div className="inline-flex items-center gap-2 bg-surface-card border border-white/5 rounded-full px-4 py-1.5 text-xs font-medium text-slate-300 mb-8 mt-10">
                        <span className="text-brand-500">🛡️</span> Setting a new standard for honest online exams
                    </div>

                    {/* Headline */}
                    <h1 className="text-5xl md:text-7xl font-semibold leading-[1.1] tracking-tight mb-6">
                        The AI Proctoring <br className="hidden md:block" />
                        <span className="text-white">your exams really need</span>
                    </h1>

                    {/* Subheadline */}
                    <p className="text-lg text-slate-400 max-w-2xl mx-auto mb-10 leading-relaxed">
                        We help universities run honest exams from anywhere. Our smart proctor acts like a quiet observer, securing assessments fairly while significantly reducing student anxiety.
                    </p>

                    {/* CTA Buttons */}
                    <div className="flex flex-col sm:flex-row items-center justify-center gap-4 mb-20 w-full sm:w-auto">
                        <button
                            onClick={() => window.open('/login', '_blank')}
                            className="bg-brand-500 hover:bg-brand-400 text-black px-8 py-3.5 rounded-full font-semibold text-base transition shadow-[0_0_20px_rgba(5,208,104,0.3)] hover:shadow-[0_0_30px_rgba(5,208,104,0.5)] w-full sm:w-auto"
                        >
                            Get Started
                        </button>
                        <button
                            onClick={() => navigate('/demo-dashboard')}
                            className="bg-surface-card border border-white/5 hover:border-white/10 text-white px-8 py-3.5 rounded-full font-medium text-base transition w-full sm:w-auto"
                        >
                            Learn More
                        </button>
                    </div>

                    {/* Dashboard Preview Mockup */}
                    <div className="w-full max-w-4xl bg-surface-card/80 backdrop-blur-md rounded-2xl border border-white/5 shadow-2xl overflow-hidden mt-6 animate-slide-up relative">
                        {/* Mockup Header */}
                        <div className="h-12 border-b border-white/5 flex items-center px-4 gap-2 bg-surface-dark/50">
                            <div className="flex gap-1.5">
                                <div className="w-3 h-3 rounded-full bg-slate-700/50"></div>
                                <div className="w-3 h-3 rounded-full bg-slate-700/50"></div>
                                <div className="w-3 h-3 rounded-full bg-slate-700/50"></div>
                            </div>
                            <div className="ml-4 flex items-center gap-2">
                                <div className="w-4 h-4 rounded-full bg-brand-500/20 flex items-center justify-center"><div className="w-1.5 h-1.5 bg-brand-500 rounded-full"></div></div>
                                <span className="text-xs font-mono text-brand-500">Live Session Active</span>
                            </div>
                        </div>
                        {/* Mockup Body Grid */}
                        <div className="p-4 md:p-6 grid grid-cols-12 gap-4 h-auto md:h-[350px]">
                            {/* Left Panel: Stats */}
                            <div className="col-span-12 md:col-span-3 flex flex-col gap-3">
                                <div className="text-white/80 font-medium text-sm mb-2 flex items-center gap-2">
                                    <span className="w-5 h-5 rounded bg-brand-500/20 text-brand-500 flex items-center justify-center text-xs">A</span>
                                    TrustIQ Panel
                                </div>
                                <div className="bg-white/5 rounded-lg p-3 border border-white/5 border-l-2 border-l-brand-500 flex flex-col">
                                    <span className="text-slate-500 text-[10px] uppercase font-bold tracking-wider mb-1">Integrity Score</span>
                                    <span className="text-brand-500 text-2xl font-mono">98%</span>
                                </div>
                                <div className="bg-white/5 rounded-lg p-3 border border-white/5 flex flex-col">
                                    <span className="text-slate-500 text-[10px] uppercase font-bold tracking-wider mb-1">System Status</span>
                                    <span className="text-white text-sm">Monitoring Active</span>
                                </div>
                                <div className="bg-white/5 rounded-lg p-3 border border-white/5 flex flex-col">
                                    <span className="text-slate-500 text-[10px] uppercase font-bold tracking-wider mb-2">Metrics</span>
                                    <div className="h-1.5 w-full bg-slate-800 rounded-full overflow-hidden flex">
                                        <div className="h-full bg-brand-500 w-[98%]"></div>
                                        <div className="h-full bg-amber-500 w-[2%]"></div>
                                    </div>
                                    <div className="flex justify-between mt-2 text-[10px]">
                                        <span className="text-brand-500">Verified</span>
                                        <span className="text-amber-500">Flags</span>
                                    </div>
                                </div>
                            </div>

                            {/* Center & Right Panel */}
                            <div className="col-span-12 md:col-span-9 grid grid-cols-2 gap-4">
                                {/* Live Feed Mock */}
                                <div className="bg-white/[0.02] rounded-xl border border-white/5 relative overflow-hidden flex flex-col">
                                    <div className="p-3 border-b border-white/5 flex justify-between items-center text-xs text-slate-400">
                                        <span>Live Event Stream</span>
                                        <span className="w-2 h-2 rounded-full bg-brand-500 animate-pulse"></span>
                                    </div>
                                    <div className="flex-1 p-3 flex flex-col gap-2 overflow-hidden relative">
                                        <div className="w-full h-1/2 bg-gradient-to-t from-brand-500/10 to-transparent absolute bottom-0 left-0 pointer-events-none"></div>
                                        {/* Mock Logs */}
                                        <div className="text-[11px] text-slate-300 font-mono bg-white/5 p-2 rounded-md border-l-2 border-brand-500/50">
                                            <span className="text-brand-500 opacity-70">10:45:01</span> Face verified matching ID
                                        </div>
                                        <div className="text-[11px] text-slate-300 font-mono bg-white/5 p-2 rounded-md border-l-2 border-brand-500/50">
                                            <span className="text-brand-500 opacity-70">10:45:15</span> Audio levels stable (40dB)
                                        </div>
                                        <div className="text-[11px] text-slate-300 font-mono bg-white/5 p-2 rounded-md border-l-2 border-brand-500/50">
                                            <span className="text-brand-500 opacity-70">10:46:12</span> Attention metrics positive
                                        </div>
                                    </div>
                                </div>

                                {/* Vision/Camera Feed Mock */}
                                <div className="bg-white/[0.02] rounded-xl border border-white/5 p-3 flex flex-col">
                                    <div className="text-xs text-slate-400 mb-2">Student View</div>
                                    <div className="flex-1 rounded-lg border border-white/10 bg-black/50 relative overflow-hidden flex items-center justify-center group">
                                        <div className="absolute inset-x-8 inset-y-6 border border-brand-500/40 rounded-lg group-hover:scale-105 transition-transform duration-500">
                                            <div className="absolute -top-3 left-1/2 -translate-x-1/2 bg-surface-dark px-2 text-[8px] text-brand-500 font-mono border border-brand-500/40 rounded">FACE_DETECTED</div>
                                        </div>
                                        <div className="absolute inset-0 bg-gradient-to-b from-transparent to-brand-500/5 MIX-blend-overlay"></div>
                                        <span className="text-4xl opacity-20 group-hover:opacity-100 transition-opacity">👤</span>
                                    </div>
                                </div>

                                {/* Activity Chart Mock */}
                                <div className="col-span-2 bg-white/[0.02] rounded-xl border border-white/5 p-3 flex flex-col h-28 hidden md:flex">
                                    <div className="text-xs text-slate-400 flex justify-between items-center mb-auto">
                                        <span>Timeline Analysis</span>
                                        <span className="text-[10px] text-slate-500 font-mono">Last 60 Minutes</span>
                                    </div>
                                    <div className="flex items-end gap-1 h-12 w-full mt-2">
                                        {[40, 45, 55, 50, 42, 38, 45, 60, 55, 48, 50, 45, 40, 42, 55, 60, 65, 50, 45, 42].map((h, i) => (
                                            <div key={i} className="flex-1 bg-brand-500/20 hover:bg-brand-500/50 transition-colors rounded-t-sm" style={{ height: `${h}%` }}></div>
                                        ))}
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </section>

            {/* ─── Features (Humanized) ─── */}
            <section id="features" className="py-24 px-6 relative z-10">
                <div className="max-w-6xl mx-auto">
                    <div className="text-center mb-16">
                        <h2 className="text-3xl md:text-4xl font-semibold mb-4 text-white tracking-tight">
                            Smart tech. <span className="text-slate-400">Zero stress.</span>
                        </h2>
                        <p className="text-slate-400 max-w-xl mx-auto text-lg">
                            We don't believe in alarming students. Our background analysis looks at multiple gentle signals to give you a reliable, fair integrity report.
                        </p>
                    </div>

                    <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
                        {FEATURES.map(f => (
                            <div key={f.title} className="bg-[#080808] border border-white/5 rounded-2xl p-8 hover:border-brand-500/30 transition-all duration-300 hover:shadow-2xl hover:shadow-brand-500/5 group relative overflow-hidden">
                                <div className={`w-12 h-12 rounded-xl bg-gradient-to-br ${f.color} flex items-center justify-center text-2xl mb-6 shadow-lg shadow-brand-500/10 group-hover:scale-110 transition-transform`}>
                                    {f.icon}
                                </div>
                                <h3 className="text-lg font-medium text-white mb-3 tracking-tight">{f.title}</h3>
                                <p className="text-slate-400 leading-relaxed font-light">{f.desc}</p>
                            </div>
                        ))}
                    </div>
                </div>
            </section>

            {/* ─── How It Works ─── */}
            <section id="how-it-works" className="py-32 px-6">
                <div className="max-w-5xl mx-auto">
                    <div className="text-center mb-16">
                        <h2 className="text-3xl md:text-4xl font-semibold mb-4 tracking-tight">How simple is it?</h2>
                        <p className="text-slate-400 font-light text-lg">Four invisible steps to a completely secure and fair assessment.</p>
                    </div>

                    <div className="grid md:grid-cols-4 gap-8 relative">
                        {/* Connecting Line */}
                        <div className="hidden md:block absolute top-6 left-[10%] right-[10%] h-[1px] bg-gradient-to-r from-transparent via-white/10 to-transparent"></div>

                        {STEPS.map((step, i) => (
                            <div key={step.num} className="relative z-10 flex flex-col items-center text-center">
                                <div className="w-12 h-12 rounded-full bg-surface-dark border border-white/10 flex items-center justify-center text-sm font-medium text-slate-300 mb-6 shadow-xl">
                                    {step.num}
                                </div>
                                <h3 className="text-lg font-medium text-white mb-2">{step.title}</h3>
                                <p className="text-slate-400 text-sm leading-relaxed font-light">{step.desc}</p>
                            </div>
                        ))}
                    </div>
                </div>
            </section>

            {/* ─── Pricing ─── */}
            <section id="pricing" className="py-24 px-6">
                <div className="max-w-5xl mx-auto">
                    <div className="text-center mb-16">
                        <h2 className="text-3xl md:text-4xl font-semibold mb-4 tracking-tight">
                            Pricing that makes sense
                        </h2>
                        <p className="text-slate-400 font-light text-lg">Scalable integrity for institutions of any size.</p>
                    </div>

                    <div className="grid md:grid-cols-3 gap-6">
                        {PRICING.map(plan => (
                            <div
                                key={plan.name}
                                className={`rounded-2xl p-8 border transition-all duration-300 flex flex-col relative overflow-hidden ${plan.highlight
                                    ? 'bg-[#080808] border-brand-500/40 shadow-2xl shadow-brand-500/10 scale-[1.02]'
                                    : 'bg-[#050505] border-white/5 hover:border-white/10'
                                    }`}
                            >
                                {plan.highlight && (
                                    <div className="absolute top-0 right-0 w-32 h-32 bg-brand-500/10 rounded-full blur-2xl pointer-events-none"></div>
                                )}
                                {plan.highlight && (
                                    <div className="text-xs font-medium text-brand-400 uppercase tracking-wider mb-4">Most Popular</div>
                                )}
                                {!plan.highlight && <div className="mb-4 text-transparent text-xs">Spacer</div>}
                                
                                <h3 className="text-xl font-medium text-white mb-1">{plan.name}</h3>
                                <p className="text-sm text-slate-400 mb-6 font-light">{plan.desc}</p>
                                
                                <div className="mb-8 flex items-baseline">
                                    <span className="text-4xl font-semibold font-mono tracking-tighter text-white">{plan.price}</span>
                                    <span className="text-slate-500 text-sm ml-1 font-light">{plan.period}</span>
                                </div>
                                
                                <ul className="space-y-4 mb-8 flex-1">
                                    {plan.features.map(f => (
                                        <li key={f} className="flex items-start gap-3 text-sm text-slate-300 font-light">
                                            <div className="w-5 h-5 rounded-full bg-brand-500/10 flex items-center justify-center flex-shrink-0 mt-0.5">
                                                <span className="text-brand-500 text-[10px]">✓</span>
                                            </div>
                                            {f}
                                        </li>
                                    ))}
                                </ul>
                                
                                <button
                                    onClick={() => window.open('/login', '_blank')}
                                    className={`w-full py-3.5 rounded-full font-medium transition text-sm ${plan.highlight
                                        ? 'bg-brand-500 hover:bg-brand-400 text-black shadow-lg shadow-brand-500/20'
                                        : 'bg-white/5 hover:bg-white/10 text-white'
                                        }`}
                                >
                                    {plan.cta}
                                </button>
                            </div>
                        ))}
                    </div>
                </div>
            </section>

            {/* ─── Footer ─── */}
            <footer className="border-t border-white/5 py-12 px-6 bg-[#020202]">
                <div className="max-w-6xl mx-auto flex flex-col md:flex-row justify-between items-center gap-6">
                    <div className="flex items-center gap-2">
                        <div className="w-6 h-6 rounded border border-brand-500/30 bg-brand-500/10 flex items-center justify-center">
                            <div className="w-2 h-2 bg-brand-400 rounded-full blur-[1px]"></div>
                        </div>
                        <span className="font-medium text-slate-200">TrustIQ.</span>
                    </div>
                    <div className="text-sm text-slate-500 font-light">
                        © 2026 TrustIQ SaaS. Made by Pradnyesh.K.
                    </div>
                </div>
            </footer>
        </div>
    )
}
