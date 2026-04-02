// useMediaCapture — Webcam + Microphone capture hook
// Captures video frames as base64 and audio chunks as Float32 → base64

import { useState, useRef, useCallback, useEffect, useMemo } from 'react'

export default function useMediaCapture({ onFrame, onAudioChunk, frameIntervalMs = 500, audioIntervalMs = 2000 }) {
    const [isActive, setIsActive] = useState(false)
    const [error, setError] = useState(null)
    const [hasPermission, setHasPermission] = useState(false)
    const [stream, setStream] = useState(null)

    // Internal video element strictly for frame capture (invisible to UI)
    const internalVideoRef = useRef(document.createElement('video'))
    const streamRef = useRef(null)
    const frameTimerRef = useRef(null)
    const audioTimerRef = useRef(null)
    const audioContextRef = useRef(null)
    const analyserRef = useRef(null)
    const canvasRef = useRef(document.createElement('canvas'))

    useEffect(() => {
        internalVideoRef.current.muted = true
        internalVideoRef.current.playsInline = true
        internalVideoRef.current.autoplay = true
    }, [])

    const captureFrame = useCallback(() => {
        const video = internalVideoRef.current
        if (!video || video.readyState < 2) return

        const canvas = canvasRef.current
        canvas.width = 320  // Downscale for transmission
        canvas.height = 240
        const ctx = canvas.getContext('2d')
        ctx.drawImage(video, 0, 0, 320, 240)

        const base64 = canvas.toDataURL('image/jpeg', 0.6).split(',')[1]
        if (onFrame) onFrame(base64)
    }, [onFrame])

    const captureAudio = useCallback(() => {
        const analyser = analyserRef.current
        if (!analyser) return

        const bufferLength = analyser.fftSize
        const dataArray = new Float32Array(bufferLength)
        analyser.getFloatTimeDomainData(dataArray)

        // Convert Float32Array to base64
        const bytes = new Uint8Array(dataArray.buffer)
        let binary = ''
        for (let i = 0; i < bytes.byteLength; i++) {
            binary += String.fromCharCode(bytes[i])
        }
        const base64 = btoa(binary)
        if (onAudioChunk) onAudioChunk(base64)
    }, [onAudioChunk])

    const start = useCallback(async () => {
        try {
            const mediaStream = await navigator.mediaDevices.getUserMedia({
                video: { width: 640, height: 480, facingMode: 'user' },
                audio: { sampleRate: 16000, channelCount: 1, echoCancellation: true, noiseSuppression: true }
            })

            streamRef.current = mediaStream
            setStream(mediaStream)
            setHasPermission(true)
            setIsActive(true)

            // Attach video to hidden internal element for frame capture
            internalVideoRef.current.srcObject = mediaStream
            internalVideoRef.current.play().catch(e => console.warn('Internal video play issue:', e))

            // Frame capture timer
            frameTimerRef.current = setInterval(() => {
                captureFrame()
            }, frameIntervalMs)

            // Audio capture setup
            const audioCtx = new (window.AudioContext || window.webkitAudioContext)({ sampleRate: 16000 })
            audioContextRef.current = audioCtx
            const source = audioCtx.createMediaStreamSource(mediaStream)
            const analyser = audioCtx.createAnalyser()
            analyser.fftSize = 4096
            source.connect(analyser)
            analyserRef.current = analyser

            // Audio chunk timer
            audioTimerRef.current = setInterval(() => {
                captureAudio()
            }, audioIntervalMs)

        } catch (err) {
            console.error('Media capture error:', err)
            setError(err.message === 'Permission denied'
                ? 'Camera and microphone access is required for exam proctoring.'
                : `Media error: ${err.message}`)
        }
    }, [frameIntervalMs, audioIntervalMs, captureFrame, captureAudio])

    const stop = useCallback(() => {
        if (frameTimerRef.current) clearInterval(frameTimerRef.current)
        if (audioTimerRef.current) clearInterval(audioTimerRef.current)
        if (audioContextRef.current) audioContextRef.current.close()
        if (streamRef.current) {
            streamRef.current.getTracks().forEach(t => t.stop())
        }
        setIsActive(false)
    }, [])



    useEffect(() => {
        return () => stop()
    }, [stop])

    return useMemo(() => ({ stream, isActive, hasPermission, error, start, stop }), [stream, isActive, hasPermission, error, start, stop])
}
