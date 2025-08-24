import { createContext, useCallback, useContext, useMemo, useState } from 'react'

type Toast = { id: number; message: string; tone?: 'info' | 'warning' | 'error' }

const ToastCtx = createContext<{
  toasts: Toast[]
  show: (message: string, tone?: Toast['tone']) => void
  remove: (id: number) => void
} | null>(null)

export function ToastProvider({ children }: { children: React.ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([])
  const remove = useCallback((id: number) => setToasts((prev) => prev.filter((t) => t.id !== id)), [])
  const show = useCallback((message: string, tone: Toast['tone'] = 'info') => {
    const id = Date.now() + Math.random()
    setToasts((prev) => [...prev, { id, message, tone }])
    setTimeout(() => remove(id), 4000)
  }, [remove])
  const value = useMemo(() => ({ toasts, show, remove }), [toasts, show, remove])
  return (
    <ToastCtx.Provider value={value}>
      {children}
      <div className="fixed bottom-4 right-4 z-[100] space-y-2">
        {toasts.map((t) => (
          <div key={t.id} className={`rounded-md px-3 py-2 shadow border text-sm ${t.tone === 'error' ? 'bg-red-50 border-red-600 text-red-800' : t.tone === 'warning' ? 'bg-yellow-50 border-yellow-700 text-yellow-900' : 'bg-[#FFF8EB] border-[#633D00] text-[#633D00]'}`}>
            {t.message}
          </div>
        ))}
      </div>
    </ToastCtx.Provider>
  )
}

export function useToast() {
  const ctx = useContext(ToastCtx)
  if (!ctx) throw new Error('useToast must be used within ToastProvider')
  return ctx
}


