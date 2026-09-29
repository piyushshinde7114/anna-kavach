import { useEffect, useState } from 'react'

export function Laminate({ layers }) {
  return (
    <div className="lam" aria-label={`Layers: ${layers.map((l) => l.name).join(', ')}`}>
      {layers.map((l, i) => (
        <div key={i} className={`strip f-${l.family.replace('+', '')} ${l.name.startsWith('met') || l.family === 'AL' ? 'metal' : ''}`}
          style={{ width: `${Math.max(58, 100 - i * 6)}%` }} title={l.name}>{l.name}</div>
      ))}
    </div>
  )
}

export const Conf = ({ c }) => {
  const label = { sourced: 'sourced', typical: 'typical', assumed: 'assumed', demo: 'demo', user: 'your input', estimated: 'estimated' }[c] || c
  return <span className={`conf ${c}`}>{label}</span>
}

export function Tape({ children }) { return <div className="tape">{children}</div> }

export function useToast() {
  const [msg, setMsg] = useState(null)
  useEffect(() => { if (!msg) return; const t = setTimeout(() => setMsg(null), 2600); return () => clearTimeout(t) }, [msg])
  return [msg ? <div className="toast" role="status">{msg}</div> : null, setMsg]
}

export function Skeleton({ lines = 4 }) {
  return <div className="sheet stack" aria-busy="true">{Array.from({ length: lines }, (_, i) => <div key={i} className="skeleton" style={{ width: `${90 - i * 12}%` }} />)}</div>
}
