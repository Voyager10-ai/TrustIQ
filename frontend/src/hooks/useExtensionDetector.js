import { useState, useEffect } from 'react'

// Known extension IDs or DOM markers for common cheat/helper extensions
const KNOWN_EXTENSIONS = [
    { id: 'bhjlkfgalhoflgholjfkceehhiamkfce', name: 'Grammarly' }, // Example ID, might vary natively but we check the DOM instead
    { id: 'fmkadmapgofadopljbjfkapdkoienihi', name: 'React DevTools' }
]

export default function useExtensionDetector() {
    const [detectedExtensions, setDetectedExtensions] = useState([])

    useEffect(() => {
        const detect = () => {
            const detected = []

            // 1. Check for Grammarly (adds specific attributes to body or inputs)
            if (document.querySelector('grammarly-desktop-integration') || document.body.hasAttribute('data-new-gr-c-s-check-loaded')) {
                detected.push('Grammarly Assistant')
            }

            // 2. Check for React DevTools (often used for debugging/inspecting state)
            if (window.__REACT_DEVTOOLS_GLOBAL_HOOK__) {
                detected.push('React Developer Tools')
            }

            // 3. Check for specific AI extensions (like ChatGPT Sidebar, Monica, Sider, Harpa, Merlin)
            // Many inject a shadow DOM, a sidebar container, or custom buttons
            const aiMarkers = [
                '#sider-app',
                '#monica-content-root',
                '#harpa-root',
                '#merlin-shadow-host',
                '.chatgpt-sidebar-container',
                '#chatgpt-sidebar',
                'chatgpt-sidebar-app', // custom element
                '[data-testid="chatgpt-sidebar-root"]',
                '.sider-container',
                '#gpt-sidebar-container'
            ]

            for (const marker of aiMarkers) {
                if (document.querySelector(marker)) {
                    detected.push('AI ChatGPT Extension / Sidebar')
                    break
                }
            }

            // 4. Generic Heuristic: Detect unexplained Shadow DOMs or Custom Elements injected into body
            // Extensions almost always append their UI directly to the body or html tag.
            // Our app only expects <div id="root"> and maybe some Vite <script> tags.
            const suspiciousTags = []
            for (const child of document.body.children) {
                const tag = child.tagName.toLowerCase()
                // Ignore our React root, scripts, styles, and noscript tags
                if (child.id !== 'root' && tag !== 'script' && tag !== 'style' && tag !== 'noscript') {
                    // If it's a custom element (contains a hyphen) or has an open shadow root
                    if (tag.includes('-') || child.shadowRoot) {
                        suspiciousTags.push(tag)
                    }
                }
            }
            if (suspiciousTags.length > 0) {
                detected.push('Generic Injected Overlay / Custom Extension')
            }

            // 5. Try fetching web accessible resources (Modern extensions often block this, but it's a fallback)
            KNOWN_EXTENSIONS.forEach(async (ext) => {
                try {
                    // Attempting to fetch a manifest or known icon (this throws CORS if blocked, or 404 if not found)
                    // Some extensions explicitly expose a web_accessible_resource for detection
                    const res = await fetch(`chrome-extension://${ext.id}/manifest.json`)
                    if (res.ok && !detected.includes(ext.name)) {
                        detected.push(ext.name)
                    }
                } catch {
                    // Network error or blocked by CORS — expected if extension is missing
                }
            })

            if (detected.length > 0) {
                setDetectedExtensions(prev => {
                    const newSet = new Set([...prev, ...detected])
                    const newArr = Array.from(newSet)
                    if (prev.length === newArr.length && prev.every((v, i) => v === newArr[i])) return prev
                    return newArr
                })
            }
        }

        // Run detection initially and also observe DOM changes for dynamically injected extensions
        detect()

        const observer = new MutationObserver(() => {
            detect()
        })
        observer.observe(document.body, { childList: true, subtree: true })

        return () => observer.disconnect()
    }, [])

    return { detectedExtensions }
}
