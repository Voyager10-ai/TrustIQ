// useKeystrokeTracker — Tracks typing rhythm, clipboard, and tab visibility

import { useState, useRef, useCallback, useEffect, useMemo } from 'react'

export default function useKeystrokeTracker({ onBatch, batchIntervalMs = 2000 }) {
    const [isTracking, setIsTracking] = useState(false)
    const [stats, setStats] = useState({ keyCount: 0, pasteCount: 0, tabSwitches: 0 })

    const bufferRef = useRef([])
    const lastKeyTimeRef = useRef(null)
    const keyDownTimesRef = useRef({})
    const timerRef = useRef(null)
    const statsRef = useRef({ keyCount: 0, pasteCount: 0, tabSwitches: 0 })

    const handleKeyDown = useCallback((e) => {
        const now = performance.now()
        keyDownTimesRef.current[e.key] = now

        const entry = {
            key: e.key.length === 1 ? 'char' : e.key, // Don't send actual characters for privacy
            timestamp: now,
            interKeyInterval: lastKeyTimeRef.current ? now - lastKeyTimeRef.current : 0,
            isSpecial: e.ctrlKey || e.metaKey || e.altKey
        }

        // Detect Ctrl+V / Cmd+V
        if ((e.ctrlKey || e.metaKey) && e.key === 'v') {
            entry.isPaste = true
            statsRef.current.pasteCount++
        }

        bufferRef.current.push(entry)
        lastKeyTimeRef.current = now
        statsRef.current.keyCount++
        setStats({ ...statsRef.current })
    }, [])

    const handleKeyUp = useCallback((e) => {
        const downTime = keyDownTimesRef.current[e.key]
        if (downTime) {
            const holdTime = performance.now() - downTime
            // Attach hold time to last matching entry
            const entries = bufferRef.current
            for (let i = entries.length - 1; i >= 0; i--) {
                if (entries[i].key === (e.key.length === 1 ? 'char' : e.key) && !entries[i].holdTime) {
                    entries[i].holdTime = holdTime
                    break
                }
            }
            delete keyDownTimesRef.current[e.key]
        }
    }, [])

    const handlePaste = useCallback((e) => {
        const pastedText = e.clipboardData?.getData('text') || ''
        bufferRef.current.push({
            key: 'PASTE',
            timestamp: performance.now(),
            pastedLength: pastedText.length,
            isPaste: true
        })
        statsRef.current.pasteCount++
        setStats({ ...statsRef.current })
    }, [])

    const handleVisibilityChange = useCallback(() => {
        if (document.hidden) {
            bufferRef.current.push({
                key: 'TAB_SWITCH_AWAY',
                timestamp: performance.now(),
                isTabSwitch: true
            })
            statsRef.current.tabSwitches++
            setStats({ ...statsRef.current })
        } else {
            bufferRef.current.push({
                key: 'TAB_SWITCH_BACK',
                timestamp: performance.now(),
                isTabSwitch: true
            })
        }
    }, [])

    const handleWindowBlur = useCallback(() => {
        // Only count if document isn't already hidden (to avoid double counting with visibilitychange)
        if (!document.hidden) {
            bufferRef.current.push({
                key: 'WINDOW_BLUR',
                timestamp: performance.now(),
                isTabSwitch: true // We treat window blur the same as a tab switch for risk scoring
            })
            statsRef.current.tabSwitches++
            setStats({ ...statsRef.current })
        }
    }, [])

    const handleWindowFocus = useCallback(() => {
        if (!document.hidden) {
            bufferRef.current.push({
                key: 'WINDOW_FOCUS',
                timestamp: performance.now(),
                isTabSwitch: true
            })
        }
    }, [])

    const flush = useCallback(() => {
        if (bufferRef.current.length === 0) return
        const batch = [...bufferRef.current]
        bufferRef.current = []
        if (onBatch) onBatch(batch)
    }, [onBatch])

    const start = useCallback(() => {
        setIsTracking(true)
        statsRef.current = { keyCount: 0, pasteCount: 0, tabSwitches: 0 }
        document.addEventListener('keydown', handleKeyDown)
        document.addEventListener('keyup', handleKeyUp)
        document.addEventListener('paste', handlePaste)
        document.addEventListener('visibilitychange', handleVisibilityChange)
        window.addEventListener('blur', handleWindowBlur)
        window.addEventListener('focus', handleWindowFocus)
        timerRef.current = setInterval(flush, batchIntervalMs)
    }, [handleKeyDown, handleKeyUp, handlePaste, handleVisibilityChange, handleWindowBlur, handleWindowFocus, flush, batchIntervalMs])

    const stop = useCallback(() => {
        setIsTracking(false)
        document.removeEventListener('keydown', handleKeyDown)
        document.removeEventListener('keyup', handleKeyUp)
        document.removeEventListener('paste', handlePaste)
        document.removeEventListener('visibilitychange', handleVisibilityChange)
        window.removeEventListener('blur', handleWindowBlur)
        window.removeEventListener('focus', handleWindowFocus)
        if (timerRef.current) clearInterval(timerRef.current)
        flush()
    }, [handleKeyDown, handleKeyUp, handlePaste, handleVisibilityChange, handleWindowBlur, handleWindowFocus, flush])

    useEffect(() => {
        return () => stop()
    }, [stop])

    return useMemo(() => ({ isTracking, stats, start, stop }), [isTracking, stats, start, stop])
}
