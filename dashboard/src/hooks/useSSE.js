/**
 * useSSE — Server-Sent Events hook (DISABLED for stability)
 *
 * SSE will be re-enabled after optimizing the backend connection pool.
 * For now, pages use manual refresh.
 */
export default function useSSE() {
    // Intentionally disabled — SSE saturates API workers
    // TODO: Re-enable with dedicated SSE server or WebSocket
}
