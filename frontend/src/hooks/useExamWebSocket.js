// useExamWebSocket — Multiplexed WebSocket connection for exam data streaming

import { useState, useRef, useCallback, useEffect, useMemo } from 'react'

const DEFAULT_WS_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8000'

export default function useExamWebSocket({ sessionId, backendUrl = DEFAULT_WS_URL }) {
    const [isConnected, setIsConnected] = useState(false)
    const [riskData, setRiskData] = useState(null)
    const [lastError, setLastError] = useState(null)

    const wsRef = useRef(null)
    const reconnectRef = useRef(null)
    const reconnectAttempts = useRef(0)

    const connect = useCallback(function doConnect() {
        if (!sessionId) return

        try {
            const ws = new WebSocket(`${backendUrl}/ws/exam/${sessionId}`)
            wsRef.current = ws

            ws.onopen = () => {
                console.log('[WS] Connected to TrustIQ backend')
                setIsConnected(true)
                setLastError(null)
                reconnectAttempts.current = 0
            }

            ws.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data)
                    if (data.type === 'risk_update') {
                        setRiskData(data)
                    }
                } catch (e) {
                    console.warn('[WS] Parse error:', e)
                }
            }

            ws.onclose = () => {
                console.log('[WS] Disconnected')
                setIsConnected(false)
                // Auto-reconnect with backoff
                if (reconnectAttempts.current < 10) {
                    const delay = Math.min(1000 * Math.pow(2, reconnectAttempts.current), 30000)
                    reconnectRef.current = setTimeout(() => {
                        reconnectAttempts.current++
                        doConnect()
                    }, delay)
                }
            }

            ws.onerror = (err) => {
                console.error('[WS] Error:', err)
                setLastError('Connection error — is the backend running?')
            }
        } catch (err) {
            setLastError(`WebSocket error: ${err.message}`)
        }
    }, [sessionId, backendUrl])

    const disconnect = useCallback(() => {
        if (reconnectRef.current) clearTimeout(reconnectRef.current)
        if (wsRef.current) {
            wsRef.current.close()
            wsRef.current = null
        }
        setIsConnected(false)
    }, [])

    // Send methods for different data types
    const sendFrame = useCallback((frameBase64) => {
        if (wsRef.current?.readyState === WebSocket.OPEN) {
            wsRef.current.send(JSON.stringify({ type: 'frame', data: frameBase64, timestamp: Date.now() }))
        }
    }, [])

    const sendAudio = useCallback((audioBase64) => {
        if (wsRef.current?.readyState === WebSocket.OPEN) {
            wsRef.current.send(JSON.stringify({ type: 'audio', data: audioBase64, timestamp: Date.now() }))
        }
    }, [])

    const sendKeystrokes = useCallback((batch) => {
        if (wsRef.current?.readyState === WebSocket.OPEN) {
            wsRef.current.send(JSON.stringify({ type: 'keystrokes', data: batch, timestamp: Date.now() }))
        }
    }, [])

    const sendMouseData = useCallback((batch) => {
        if (wsRef.current?.readyState === WebSocket.OPEN) {
            wsRef.current.send(JSON.stringify({ type: 'mouse', data: batch, timestamp: Date.now() }))
        }
    }, [])

    const sendText = useCallback((text) => {
        if (wsRef.current?.readyState === WebSocket.OPEN) {
            wsRef.current.send(JSON.stringify({ type: 'text', data: text, timestamp: Date.now() }))
        }
    }, [])

    useEffect(() => {
        return () => disconnect()
    }, [disconnect])

    return useMemo(() => ({
        isConnected, riskData, lastError, connect, disconnect, sendFrame, sendAudio, sendKeystrokes, sendMouseData, sendText
    }), [isConnected, riskData, lastError, connect, disconnect, sendFrame, sendAudio, sendKeystrokes, sendMouseData, sendText])
}
