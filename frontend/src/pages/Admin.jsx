import { useEffect, useState } from 'react'
import { api } from '../api.js'

export default function Admin() {
  const [tok, setTok] = useState(() => { try { return sessionStorage.getItem('ak-admin') || '' } catch { return '' } })
  const [ok, setOk] = useState(false)
  const [err, setErr] = useState(null)
  const [films, setFilms] = useState([])
  const [edit, setEdit] = useState({})
  const [saved, setSaved] = useState(null)
  const login = async (e) => {
    e?.preventDefault(); setErr(null)
    try { await api.adminCheck(tok); setOk(true); try { sessionStorage.setItem('ak-admin', tok) } catch {} ; setFilms(await api.films()) } catch { setErr('That admin token was not accepted.') }
  }
  useEffect(() => { if (tok) login() }, [])
  const val = (f, k, j) => edit[f.id]?.[k]?.[j] ?? f[k][j]
  const set = (f, k, j, v) => setEdit((e) => { const cur = e[f.id]?.[k] ?? [...f[k]]; const n = [...cur]; n[j] = v; return { ...e, [f.id]: { ...e[f.id], [k]: n } } })
  const save = async (f) => {
    setErr(null)
    try { const body = Object.fromEntries(Object.entries(edit[f.id] || {}).map(([k, v]) => [k, v.map(Number)])); await api.putFilm(tok, f.id, body); setSaved(f.id); setEdit((e) => ({ ...e, [f.id]: undefined })); setFilms(await api.films()) }
    catch (e2) { setErr(`${f.name}: ${e2.message}`) }
  }
  if (!ok) return (
    <div className="page" style={{ marginTop: 28, maxWidth: 560 }}>
      <form className="sheet stack" onSubmit={login}>
        <div className="tape">Data desk</div>
        <p className="muted">Admins keep film values and costs current, for example after a converter sends new datasheets or quotes.</p>
        <label className="field"><span>Admin token</span><input type="password" value={tok} onChange={(e) => setTok(e.target.value)} autoComplete="current-password" /></label>
        {err && <div className="err">{err}</div>}
        <div><button className="btn">Sign in</button></div>
      </form>
    </div>
  )
  return (
    <div className="page stack" style={{ '--g': '18px', marginTop: 20 }}>
      <h1 style={{ fontSize: 36 }}>Data desk</h1>
      <p className="muted">Edit a range and save. Every new recommendation uses the updated values; edited rows are marked in the library.</p>
      {err && <div className="err">{err}</div>}
      <div className="sheet"><div className="tscroll"><table className="t">
        <thead><tr><th>Film</th><th>OTR low / high</th><th>WVTR low / high</th><th>₹/m² low / high</th><th></th></tr></thead>
        <tbody>{films.map((f) => (
          <tr key={f.id}><td style={{ fontWeight: 600, minWidth: 160 }}>{f.name}</td>
            {['otr', 'wvtr', 'cost_m2'].map((k) => <td key={k}><div className="row" style={{ '--g': '4px', flexWrap: 'nowrap' }}>
              {[0, 1].map((j) => <input key={j} type="number" step="any" value={val(f, k, j)} onChange={(e) => set(f, k, j, e.target.value)} style={{ width: 92, padding: '6px 8px' }} aria-label={`${f.name} ${k} ${j ? 'high' : 'low'}`} />)}
            </div></td>)}
            <td>{edit[f.id] ? <button className="btn small" onClick={() => save(f)}>Save</button> : saved === f.id ? <span className="mk ok small">Saved</span> : null}</td></tr>))}</tbody>
      </table></div></div>
    </div>
  )
}
