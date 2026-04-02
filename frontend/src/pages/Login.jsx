import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { doc, setDoc } from 'firebase/firestore'
import { auth, db, googleProvider } from '../firebase'
import {
    signInWithPopup,
    signInWithEmailAndPassword,
    createUserWithEmailAndPassword,
    sendEmailVerification,
    signOut,
    onAuthStateChanged
} from 'firebase/auth'

export default function Login() {
    const [email, setEmail] = useState('')
    const [password, setPassword] = useState('')
    const [firstName, setFirstName] = useState('')
    const [lastName, setLastName] = useState('')
    const [role, setRole] = useState(() => localStorage.getItem('trustiq_role') || 'student')
    const [isSignUp, setIsSignUp] = useState(false)
    const [verificationSent, setVerificationSent] = useState(false)
    const [error, setError] = useState('')
    const [loading, setLoading] = useState(false)
    const navigate = useNavigate()

    // Persist role selection
    useEffect(() => {
        localStorage.setItem('trustiq_role', role)
    }, [role])
    // Background listener for popup completion
    // Modern browsers sometimes block the signInWithPopup Promise from resolving directly due to COOP headers
    // However, the Firebase Auth state changes successfully in the background. We catch it here!
    useEffect(() => {
        if (!auth) return
        const unsubscribe = onAuthStateChanged(auth, async (user) => {
            if (user && localStorage.getItem('trustiq_google_pending') === 'true') {
                localStorage.removeItem('trustiq_google_pending')
                const savedRole = localStorage.getItem('trustiq_role') || 'student'

                try {
                    setDoc(doc(db, 'profiles', user.uid), {
                        email: user.email,
                        firstName: user.displayName?.split(' ')[0] || '',
                        lastName: user.displayName?.split(' ').slice(1).join(' ') || '',
                        role: savedRole,
                        updatedAt: new Date().toISOString()
                    }, { merge: true }).catch(e => console.warn('Background profile creation failed:', e))
                } catch (e) {
                    console.warn('Background profile creation failed:', e)
                }

                navigate(savedRole === 'proctor' ? '/dashboard' : '/exam')
            }
        })
        return () => unsubscribe()
    }, [navigate])

    const handleError = (err) => {
        const messages = {
            'auth/user-not-found': 'No account found. Try signing up.',
            'auth/wrong-password': 'Incorrect password.',
            'auth/email-already-in-use': 'Email already registered. Try signing in.',
            'auth/weak-password': 'Password must be at least 6 characters.',
            'auth/invalid-email': 'Invalid email address.',
            'auth/invalid-credential': 'Invalid credentials. Please check your email and password.',
        }
        setError(messages[err.code] || err.message)
    }

    const handleSubmit = async (e) => {
        e.preventDefault()
        setError('')
        setLoading(true)

        try {
            if (isSignUp) {
                if (!firstName || !lastName || !email || !password) {
                    setError('All fields are required for sign up.')
                    setLoading(false)
                    return
                }

                if (password.length < 6) {
                    setError('Password must be at least 6 characters.')
                    setLoading(false)
                    return
                }

                const userCredential = await createUserWithEmailAndPassword(auth, email, password)
                await sendEmailVerification(userCredential.user)
                await signOut(auth)

                localStorage.setItem('pendingProfile', JSON.stringify({
                    firstName,
                    lastName,
                    email,
                    role
                }))

                setVerificationSent(true)
                setIsSignUp(false)
            } else {
                const userCredential = await signInWithEmailAndPassword(auth, email, password)

                if (!userCredential.user.emailVerified) {
                    await sendEmailVerification(userCredential.user)
                    await signOut(auth)
                    setError('Please verify your email first.')
                    setLoading(false)
                    return
                }

                const pendingProfile = localStorage.getItem('pendingProfile')

                if (pendingProfile) {
                    const profileData = JSON.parse(pendingProfile)
                    setDoc(doc(db, 'profiles', userCredential.user.uid), {
                        ...profileData,
                        createdAt: new Date().toISOString()
                    }).catch(e => console.warn(e))
                    localStorage.removeItem('pendingProfile')
                } else {
                    setDoc(doc(db, 'profiles', userCredential.user.uid), {
                        email: userCredential.user.email,
                        role,
                        createdAt: new Date().toISOString()
                    }, { merge: true }).catch(e => console.warn(e))
                }

                navigate(role === 'proctor' ? '/dashboard' : '/exam')
            }
        } catch (err) {
            handleError(err)
        } finally {
            setLoading(false)
        }
    }

    const handleGoogleSignIn = async () => {
        setError('')
        setLoading(true)
        localStorage.setItem('trustiq_google_pending', 'true') // Signal the background listener

        try {
            if (!auth || !googleProvider) {
                setError('Firebase not configured. Check your API keys.')
                setLoading(false)
                localStorage.removeItem('trustiq_google_pending')
                return
            }

            googleProvider.setCustomParameters({ prompt: 'select_account' })

            const result = await signInWithPopup(auth, googleProvider)

            // If the browser doesn't block the promise, we process it normally here.
            // If it DOES block the promise, the useEffect background listener above will catch it instead!
            if (localStorage.getItem('trustiq_google_pending') === 'true') {
                localStorage.removeItem('trustiq_google_pending')
                const activeUser = result.user

                try {
                    setDoc(doc(db, 'profiles', activeUser.uid), {
                        email: activeUser.email,
                        firstName: activeUser.displayName?.split(' ')[0] || '',
                        lastName: activeUser.displayName?.split(' ').slice(1).join(' ') || '',
                        role,
                        updatedAt: new Date().toISOString()
                    }, { merge: true }).catch(e => console.warn('Profile creation failed:', e))
                } catch (e) {
                    console.warn('Profile creation failed:', e)
                }

                navigate(role === 'proctor' ? '/dashboard' : '/exam')
            }

        } catch (err) {
            console.error('Google Sign-In error:', err)
            localStorage.removeItem('trustiq_google_pending')
            setError(err.message || 'Sign-in failed. Please try again.')
            setLoading(false)
        }
    }

    return (
        <div className="login-page">
            <div className="login-card animate-scale-up">
                <div className="login-header">
                    <div className="header-logo"
                        style={{ width: 56, height: 56, fontSize: 28, margin: '0 auto 16px' }}>
                        T
                    </div>
                    <h1>TrustIQ</h1>
                    <p>AI Behavioural Integrity Engine</p>
                </div>

                {verificationSent && (
                    <div style={{
                        background: 'rgba(16, 185, 129, 0.2)',
                        border: '1px solid #10b981',
                        color: '#10b981',
                        padding: '12px',
                        borderRadius: '8px',
                        marginBottom: '16px',
                        textAlign: 'center',
                        fontSize: '0.95rem'
                    }}>
                        ✅ Verification email sent to <strong>{email}</strong>.<br />
                        Please check your inbox and verify before logging in.
                        <button
                            type="button"
                            onClick={() => setVerificationSent(false)}
                            style={{
                                background: 'transparent',
                                border: 'none',
                                color: '#10b981',
                                textDecoration: 'underline',
                                marginTop: '8px',
                                cursor: 'pointer',
                                display: 'block',
                                width: '100%'
                            }}>
                            Dismiss
                        </button>
                    </div>
                )}

                <form onSubmit={handleSubmit} className="login-form">

                    <div className="role-selector">
                        <button
                            type="button"
                            className={`role-btn ${role === 'student' ? 'active' : ''}`}
                            onClick={() => setRole('student')}
                        >
                            🎓 Student
                        </button>

                        <button
                            type="button"
                            className={`role-btn ${role === 'proctor' ? 'active' : ''}`}
                            onClick={() => setRole('proctor')}
                        >
                            🛡️ Proctor
                        </button>
                    </div>

                    {isSignUp && (
                        <div style={{ display: 'flex', gap: '8px' }}>
                            <input
                                className="input login-input"
                                type="text"
                                placeholder="First Name"
                                value={firstName}
                                onChange={(e) => setFirstName(e.target.value)}
                                style={{ flex: 1 }}
                            />
                            <input
                                className="input login-input"
                                type="text"
                                placeholder="Last Name"
                                value={lastName}
                                onChange={(e) => setLastName(e.target.value)}
                                style={{ flex: 1 }}
                            />
                        </div>
                    )}

                    <input
                        className="input login-input"
                        type="email"
                        placeholder="Email address"
                        value={email}
                        onChange={(e) => setEmail(e.target.value)}
                    />

                    <input
                        className="input login-input"
                        type="password"
                        placeholder="Password"
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                    />

                    {error && <div className="login-error">{error}</div>}

                    <button
                        className="btn btn-primary login-submit"
                        type="submit"
                        disabled={loading}
                    >
                        {loading ? '⏳ Please wait...' : isSignUp ? '📝 Sign Up' : '🔐 Sign In'}
                    </button>

                    <button
                        type="button"
                        className="btn btn-secondary login-submit"
                        onClick={handleGoogleSignIn}
                        style={{
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            gap: '8px',
                            background: '#ffffff',
                            color: '#1e293b'
                        }}
                    >
                        Sign in with Google
                    </button>

                    <p
                        className="login-toggle"
                        onClick={() => setIsSignUp(!isSignUp)}
                    >
                        {isSignUp
                            ? 'Already have an account? Sign in'
                            : "Don't have an account? Sign up"}
                    </p>

                </form>
            </div>
        </div>
    )
}