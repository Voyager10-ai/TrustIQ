// useMouseTracker — Mouse movement, click, and scroll tracking

import { useState, useRef, useCallback, useEffect, useMemo } from 'react'

export default function useMouseTracker({ onBatch, batchIntervalMs = 2000, throttleMs = 50 }) {
    const [isTracking, setIsTracking] = useState(false)

    const bufferRef = useRef([])
    const timerRef = useRef(null)
    const lastMoveRef = useRef(0)

    const handleMouseMove = useCallback((e) => {
        const now = performance.now()
        if (now - lastMoveRef.current < throttleMs) return
        lastMoveRef.current = now

        bufferRef.current.push({
            type: 'move',
            x: e.clientX,
            y: e.clientY,
            timestamp: now
        })
    }, [throttleMs])

    const handleClick = useCallback((e) => {
        bufferRef.current.push({
            type: 'click',
            x: e.clientX,
            y: e.clientY,
            button: e.button,
            timestamp: performance.now()
        })
    }, [])

    const handleScroll = useCallback(() => {
        bufferRef.current.push({
            type: 'scroll',
            scrollY: window.scrollY,
            timestamp: performance.now()
        })
    }, [])

    const flush = useCallback(() => {
        if (bufferRef.current.length === 0) return
        const batch = [...bufferRef.current]
        bufferRef.current = []
        if (onBatch) onBatch(batch)
    }, [onBatch])

    const start = useCallback(() => {
        setIsTracking(true)
        document.addEventListener('mousemove', handleMouseMove)
        document.addEventListener('click', handleClick)
        window.addEventListener('scroll', handleScroll, { passive: true })
        timerRef.current = setInterval(flush, batchIntervalMs)
    }, [handleMouseMove, handleClick, handleScroll, flush, batchIntervalMs])

    const stop = useCallback(() => {
        setIsTracking(false)
        document.removeEventListener('mousemove', handleMouseMove)
        document.removeEventListener('click', handleClick)
        window.removeEventListener('scroll', handleScroll)
        if (timerRef.current) clearInterval(timerRef.current)
        flush()
    }, [handleMouseMove, handleClick, handleScroll, flush])

    useEffect(() => {
        return () => stop()
    }, [stop])

    return useMemo(() => ({ isTracking, start, stop }), [isTracking, start, stop])
}
