import { createContext, useContext, useState, useCallback } from 'react'
import { CheckCircle, XCircle, AlertTriangle, Info, X } from 'lucide-react'

const ToastContext = createContext(null)

const icons = {
  success: CheckCircle,
  error: XCircle,
  warning: AlertTriangle,
  info: Info,
}

const colors = {
  success: { bg: 'bg-[#00ff88]/10', border: 'border-[#00ff88]/30', text: 'text-[#00ff88]' },
  error: { bg: 'bg-[#ff2244]/10', border: 'border-[#ff2244]/30', text: 'text-[#ff2244]' },
  warning: { bg: 'bg-[#ff8800]/10', border: 'border-[#ff8800]/30', text: 'text-[#ff8800]' },
  info: { bg: 'bg-[#3388ff]/10', border: 'border-[#3388ff]/30', text: 'text-[#3388ff]' },
}

export function ToastProvider({ children }) {
  const [toasts, setToasts] = useState([])

  const addToast = useCallback((message, type = 'info', duration = 4000) => {
    const id = Date.now() + Math.random()
    setToasts(prev => [...prev.slice(-4), { id, message, type }])
    if (duration > 0) {
      setTimeout(() => setToasts(prev => prev.filter(t => t.id !== id)), duration)
    }
  }, [])

  const removeToast = useCallback((id) => {
    setToasts(prev => prev.filter(t => t.id !== id))
  }, [])

  return (
    <ToastContext.Provider value={addToast}>
      {children}
      <div className="fixed top-4 right-4 z-[100] flex flex-col gap-2 pointer-events-none">
        {toasts.map(toast => {
          const Icon = icons[toast.type] || Info
          const color = colors[toast.type] || colors.info
          return (
            <div key={toast.id}
              className={`pointer-events-auto flex items-center gap-3 px-4 py-3 rounded-lg text-sm shadow-lg border ${color.bg} ${color.border} animate-[slideIn_0.2s_ease-out]`}>
              <Icon className={`w-4 h-4 shrink-0 ${color.text}`} />
              <span className={color.text}>{toast.message}</span>
              <button onClick={() => removeToast(toast.id)} className="ml-2 text-gray-500 hover:text-white">
                <X className="w-3 h-3" />
              </button>
            </div>
          )
        })}
      </div>
    </ToastContext.Provider>
  )
}

export function useToast() {
  const addToast = useContext(ToastContext)
  if (!addToast) throw new Error('useToast must be used within ToastProvider')
  return addToast
}
