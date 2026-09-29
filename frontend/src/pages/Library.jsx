import { useEffect, useState } from 'react'
import { api, fmt } from '../api.js'
import { Conf, Laminate, Skeleton } from '../components/bits.jsx'

export default function Library() {
  const [films, setFilms] = useState(null)
  const [foods, setFoods] = useState(null)
  const [meta, setMeta] = useState(null)
  const [tab, setTab] = useState('films')
  useEffect(() => { api.films().then(setFilms); api.foods().then(setFoods); api.meta().then(setMeta) }, [])
  return (
    <div className="page stack" style={{ '--g': '18px', marginTop: 20 }}>
      <h1 style={{ fontSize: 36 }}>Library</h1>
      <p className="muted" style={{ maxWidth: '68ch' }}>Everything the engine reasons with, and where it comes from. Values marked <Conf c="typical" /> are literature or datasheet ranges; <Conf c="demo" /> values are placeholders to replace with converter quotes; <Conf c="assumed" /> values should be measured.</p>
      <div className="tabs">{[['films', 'Films'], ['foods', 'Foods'], ['sources', 'Sources']].map(([k, l]) => <button key={k} className="chipbtn" aria-pressed={tab === k} onClick={() => setTab(k)}>{l}</button>)}</div>
      {tab === 'films' && (!films ? <Skeleton /> : (
        <div className="sheet"><div className="tscroll"><table className="t">
          <thead><tr><th>Film</th><th></th><th>OTR cc/m²·d·atm</th><th>WVTR g/m²·d</th><th>Seals</th><th>Temp range</th><th>₹/m²</th><th>kg CO₂e/kg</th><th>Values</th></tr></thead>
          <tbody>{films.map((f) => (
            <tr key={f.id}><td style={{ fontWeight: 600, minWidth: 170 }}>{f.name}</td><td style={{ width: 90 }}><Laminate layers={[{ name: f.family, family: f.family }]} /></td>
              <td className="num">{fmt(f.otr[0], 2)}–{fmt(f.otr[1], 2)}</td><td className="num">{fmt(f.wvtr[0], 2)}–{fmt(f.wvtr[1], 2)}</td>
              <td>{f.seal ? 'yes' : '—'}</td><td className="num">{f.tmin}…{f.tmax} °C</td><td className="num">{f.cost_m2[0]}–{f.cost_m2[1]}</td><td className="num">{f.co2e}</td>
              <td><Conf c={f.conf?.edited ? 'user' : 'typical'} /></td></tr>))}</tbody>
        </table></div><p className="tiny muted" style={{ marginTop: 8 }}>OTR at 23 °C, 0 % RH; WVTR at 38 °C, 90 % RH. Cost bands are demo values.</p></div>
      ))}
      {tab === 'foods' && (!foods ? <Skeleton /> : (
        <div className="grid3">{foods.map((f) => (
          <div key={f.id} className="sheet flat stack" style={{ '--g': '8px' }}>
            <div className="row" style={{ justifyContent: 'space-between' }}><b>{f.name}</b><span className="deva small muted">{f.hi}</span></div>
            <div className="small muted">{f.category} · {f.kind}</div>
            {f.kind === 'produce'
              ? <div className="small">O₂ {f.o2_window.join('–')} %, CO₂ {f.co2_window.join('–')} % · chill ≥ {f.chill_c} °C · <Conf c={f.conf.window} /></div>
              : <div className="small">{f.mi != null ? `Moisture ${f.mi} → ${f.mc} % · ` : ''}Fat {f.fat} % · O₂ risk {f.o2}</div>}
            <div className="row" style={{ '--g': '6px' }}>{f.failure_modes.map((m) => <span key={m.mode} className="pill warn" title={m.why}>{m.mode}</span>)}</div>
          </div>))}</div>
      ))}
      {tab === 'sources' && meta && (
        <div className="sheet"><ul style={{ margin: 0, paddingLeft: 18 }}>{Object.entries(meta.sources).map(([k, s]) => <li key={k} style={{ marginBottom: 6 }}><a href={s.url} target="_blank" rel="noreferrer">{s.title}</a></li>)}</ul></div>
      )}
    </div>
  )
}
