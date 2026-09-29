import { fmt } from '../api.js'

/* All charts are drawn from one linear scale per axis; labels only name values the scale reaches. */
const lin = (d0, d1, r0, r1) => (v) => r0 + ((v - d0) / (d1 - d0 || 1)) * (r1 - r0)
const niceMax = (v) => { const p = 10 ** Math.floor(Math.log10(Math.max(v, 1))); return Math.ceil(v / p) * p }

export function GasChart({ legs, sim, baseline, food }) {
  const W = 760, H = 320, L = 48, R = 18, T = 22, B = 58
  const Hh = legs.reduce((s, l) => s + l.hours, 0)
  const yMax = 22
  const X = lin(0, Hh, L, W - R), Y = lin(0, yMax, H - B, T)
  let acc = 0
  const bands = legs.map((l, i) => { const x0 = X(acc), x1 = X(acc + l.hours); acc += l.hours; return { ...l, x0, x1, i } })
  const path = (s, key) => s.t.map((t, i) => `${i ? 'L' : 'M'}${X(t).toFixed(1)},${Y(Math.min(s[key][i], yMax)).toFixed(1)}`).join('')
  const step = Hh > 120 ? 24 : 12
  const ticks = Array.from({ length: Math.floor(Hh / step) + 1 }, (_, i) => i * step)
  const [o2a, o2b] = food.o2_window
  return (
    <svg className="chart" viewBox={`0 0 ${W} ${H}`} role="img" aria-label="Oxygen and carbon dioxide inside the bag over the journey">
      {bands.map((b) => (
        <g key={b.i}>
          <rect x={b.x0} y={T} width={b.x1 - b.x0} height={H - B - T} fill={b.temp_c > 15 ? 'var(--mango-soft)' : 'var(--leaf-soft)'} opacity={b.i % 2 ? 0.7 : 1} />
          <text x={(b.x0 + b.x1) / 2} y={H - 18} textAnchor="middle" style={{ fontWeight: 600 }}>{b.temp_c}°C</text>
          <text x={(b.x0 + b.x1) / 2} y={H - 4} textAnchor="middle" fontSize="11">{b.name.length > 26 ? b.name.slice(0, 24) + '…' : b.name}</text>
        </g>
      ))}
      <rect x={L} y={Y(o2b)} width={W - L - R} height={Y(o2a) - Y(o2b)} fill="var(--leaf)" opacity=".16" />
      {[0, 5, 10, 15, 20].map((v) => (
        <g key={v}><line className="ax" x1={L} x2={W - R} y1={Y(v)} y2={Y(v)} strokeDasharray={v ? '2 4' : ''} /><text x={L - 8} y={Y(v) + 4} textAnchor="end">{v}%</text></g>
      ))}
      {ticks.map((h) => <text key={h} x={X(h)} y={H - B + 16} textAnchor="middle" fontSize="11">{h} h</text>)}
      <line x1={L} x2={W - R} y1={Y(food.o2_min)} y2={Y(food.o2_min)} stroke="var(--chili)" strokeDasharray="5 4" strokeWidth="1.5" />
      <text x={W - R - 4} y={Y(food.o2_min) - 6} textAnchor="end" style={{ fill: 'var(--chili)', fontWeight: 600 }}>{food.o2_min}% O₂ injury limit</text>
      {baseline && <path d={path(baseline, 'o2')} fill="none" stroke="var(--chili)" strokeWidth="2" strokeDasharray="6 5" opacity=".8" />}
      {sim && <path d={path(sim, 'co2')} fill="none" stroke="var(--mango)" strokeWidth="2.6" />}
      {sim && <path d={path(sim, 'o2')} fill="none" stroke="var(--leaf)" strokeWidth="3" />}
    </svg>
  )
}

export function Histogram({ hist, horizon, target, life }) {
  const W = 560, H = 210, L = 12, R = 12, T = 18, B = 36
  const X = lin(0, horizon, L, W - R), mx = Math.max(...hist, 1), Y = lin(0, mx, H - B, T)
  const bw = (W - L - R) / hist.length
  const ticks = [0, 0.25, 0.5, 0.75, 1].map((f) => Math.round((horizon * f) / 10) * 10)
  return (
    <svg className="chart" viewBox={`0 0 ${W} ${H}`} role="img" aria-label="Spread of predicted shelf life across 1000 simulated packs">
      {hist.map((c, i) => {
        const mid = (i + 0.5) * (horizon / hist.length)
        return <rect key={i} x={L + i * bw + 1} y={Y(c)} width={bw - 2} height={H - B - Y(c)} rx="2" fill={mid < target ? 'var(--chili)' : 'var(--leaf)'} opacity={mid < target ? 0.7 : 0.85} />
      })}
      <line className="ax" x1={L} x2={W - R} y1={H - B} y2={H - B} />
      {ticks.map((t) => <text key={t} x={X(t)} y={H - B + 16} textAnchor="middle" fontSize="11">{t} d</text>)}
      <line x1={X(target)} x2={X(target)} y1={T - 8} y2={H - B} stroke="var(--ink)" strokeWidth="2" />
      <text x={X(target) + 5} y={T} style={{ fill: 'var(--ink)', fontWeight: 700 }}>target {target} d</text>
      {['p10', 'p50', 'p90'].map((k) => life[k] < horizon && (
        <g key={k}><line x1={X(life[k])} x2={X(life[k])} y1={H - B} y2={H - B + 5} stroke="var(--ink)" /></g>
      ))}
    </svg>
  )
}

export function SeasonChart({ season, target, current }) {
  const W = 560, H = 200, L = 40, R = 10, T = 16, B = 26
  const mx = niceMax(Math.max(target * 1.2, ...season.map((s) => s.life)))
  const Y = lin(0, mx, H - B, T), bw = (W - L - R) / 12
  return (
    <svg className="chart" viewBox={`0 0 ${W} ${H}`} role="img" aria-label="Predicted shelf life by dispatch month">
      {[0, mx / 2, mx].map((v) => <g key={v}><line className="ax" x1={L} x2={W - R} y1={Y(v)} y2={Y(v)} strokeDasharray={v ? '2 4' : ''} /><text x={L - 6} y={Y(v) + 4} textAnchor="end" fontSize="11">{fmt(v)}</text></g>)}
      {season.map((s, i) => (
        <g key={s.month}>
          <rect x={L + i * bw + 4} y={Y(Math.min(s.life, mx))} width={bw - 8} height={H - B - Y(Math.min(s.life, mx))} rx="3"
            fill={s.life < target ? 'var(--chili)' : 'var(--leaf)'} opacity={i === current ? 1 : 0.55} />
          <text x={L + i * bw + bw / 2} y={H - 8} textAnchor="middle" fontSize="11" style={{ fontWeight: i === current ? 700 : 400 }}>{s.month}</text>
        </g>
      ))}
      <line x1={L} x2={W - R} y1={Y(target)} y2={Y(target)} stroke="var(--ink)" strokeWidth="1.5" strokeDasharray="5 3" />
      <text x={W - R} y={Y(target) - 5} textAnchor="end" style={{ fill: 'var(--ink)', fontWeight: 600 }} fontSize="11">target {target} d</text>
    </svg>
  )
}

export function Tornado({ items, base }) {
  const W = 560, rowH = 30, L = 210, R = 20, T = 8
  const H = T + items.length * rowH + 26
  const lo = Math.min(base, ...items.map((i) => Math.min(i.low, i.high))), hi = Math.max(base, ...items.map((i) => Math.max(i.low, i.high)))
  const X = lin(lo - (hi - lo) * 0.05, hi + (hi - lo) * 0.05, L, W - R)
  return (
    <svg className="chart" viewBox={`0 0 ${W} ${H}`} role="img" aria-label="Which input moves the shelf life most">
      {items.map((it, i) => {
        const y = T + i * rowH
        const a = Math.min(it.low, it.high), b = Math.max(it.low, it.high)
        return (
          <g key={it.label}>
            <text x={L - 10} y={y + 18} textAnchor="end" fontSize="12">{it.label}</text>
            <rect x={X(Math.min(a, base))} y={y + 6} width={Math.max(1, X(base) - X(Math.min(a, base)))} height={16} rx="3" fill="var(--chili)" opacity=".75" />
            <rect x={X(base)} y={y + 6} width={Math.max(1, X(Math.max(b, base)) - X(base))} height={16} rx="3" fill="var(--leaf)" opacity=".8" />
            <text x={X(a) - 4} y={y + 18} textAnchor="end" fontSize="11">{fmt(a)}</text>
            <text x={X(b) + 4} y={y + 18} fontSize="11">{fmt(b)}</text>
          </g>
        )
      })}
      <line x1={X(base)} x2={X(base)} y1={T} y2={H - 20} stroke="var(--ink)" strokeWidth="1.5" />
      <text x={X(base)} y={H - 6} textAnchor="middle" fontSize="11" style={{ fontWeight: 700 }}>{fmt(base)} d as planned</text>
    </svg>
  )
}

export function Pareto({ points, target, selected, onSelect }) {
  const W = 560, H = 300, L = 54, R = 16, T = 16, B = 44
  const xs = points.map((p) => p.cost), ys = points.map((p) => p.co2)
  const X = lin(0, niceMax(Math.max(...xs) * 1.05), L, W - R), Y = lin(0, niceMax(Math.max(...ys) * 1.05), H - B, T)
  const xMax = niceMax(Math.max(...xs) * 1.05), yMax = niceMax(Math.max(...ys) * 1.05)
  return (
    <svg className="chart" viewBox={`0 0 ${W} ${H}`} role="img" aria-label="Cost against carbon footprint for every composed pack">
      {[0, 0.5, 1].map((f) => (
        <g key={f}>
          <line className="ax" x1={L} x2={W - R} y1={Y(yMax * f)} y2={Y(yMax * f)} strokeDasharray={f ? '2 4' : ''} />
          <text x={L - 6} y={Y(yMax * f) + 4} textAnchor="end" fontSize="11">{fmt(yMax * f, 1)}</text>
          <text x={X(xMax * f)} y={H - B + 16} textAnchor="middle" fontSize="11">₹{fmt(xMax * f, 1)}</text>
        </g>
      ))}
      <text x={(L + W - R) / 2} y={H - 6} textAnchor="middle" fontSize="12">film cost per pack</text>
      <text x={14} y={(T + H - B) / 2} textAnchor="middle" fontSize="12" transform={`rotate(-90 14 ${(T + H - B) / 2})`}>g CO₂e per pack</text>
      {points.filter((p) => !p.pass).map((p) => <circle key={p.key} cx={X(p.cost)} cy={Y(p.co2)} r="4" fill="none" stroke="var(--ink-2)" opacity=".45" />)}
      {points.filter((p) => p.pass).map((p) => (
        <circle key={p.key} cx={X(p.cost)} cy={Y(p.co2)} r={p.key === selected ? 9 : p.pareto ? 7 : 5} fill={p.pareto ? 'var(--leaf)' : 'var(--leaf-2)'}
          opacity={p.pareto ? 0.95 : 0.5} stroke={p.key === selected ? 'var(--mango)' : 'var(--sheet)'} strokeWidth={p.key === selected ? 3 : 1.5}
          style={{ cursor: 'pointer' }} onClick={() => onSelect?.(p.key)}><title>{p.name}</title></circle>
      ))}
    </svg>
  )
}
