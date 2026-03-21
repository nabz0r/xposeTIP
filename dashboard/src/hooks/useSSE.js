import { useEffect, useRef } from 'react'
import { useAuth } from '../lib/auth'

export default function useSSE(handlers = {}) {
    const { token } = useAuth()
    const handlersRef = useRef(handlers)
    handlersRef.current = handlers

    useEffect(() => {
        if (!token) return
        const baseUrl = import.meta.env.VITE_API_URL || ''
        const url = `${baseUrl}/api/v1/events/stream`
        let controller = null
        let retryTimeout = null
        let retryDelay = 1000

        function connect() {
            controller = new AbortController()
            fetch(url, {
                headers: { 'Authorization': `Bearer ${token}` },
                signal: controller.signal,
            }).then(response => {
                if (!response.ok || !response.body) {
                    throw new Error('SSE connection failed')
                }
                const reader = response.body.getReader()
                const decoder = new TextDecoder()
                let buffer = ''

                function read() {
                    reader.read().then(({ done, value }) => {
                        if (done) {
                            retryTimeout = setTimeout(connect, retryDelay)
                            return
                        }
                        buffer += decoder.decode(value, { stream: true })
                        const lines = buffer.split('\n')
                        buffer = lines.pop()
                        for (const line of lines) {
                            if (line.startsWith('data: ')) {
                                try {
                                    const event = JSON.parse(line.slice(6))
                                    const handler = handlersRef.current[event.type]
                                    if (handler) handler(event)
                                } catch { /* ignore parse errors */ }
                            }
                        }
                        retryDelay = 1000
                        read()
                    }).catch(() => {
                        retryDelay = Math.min(retryDelay * 2, 30000)
                        retryTimeout = setTimeout(connect, retryDelay)
                    })
                }
                read()
            }).catch(() => {
                retryDelay = Math.min(retryDelay * 2, 30000)
                retryTimeout = setTimeout(connect, retryDelay)
            })
        }

        connect()
        return () => {
            if (controller) controller.abort()
            if (retryTimeout) clearTimeout(retryTimeout)
        }
    }, [token])
}
