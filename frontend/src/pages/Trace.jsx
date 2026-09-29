import { useEffect, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { api, fmt, qrUrl } from '../api.js'
import { useT } from '../i18n.jsx'
import { Skeleton } from '../components/bits.jsx'

const OUTCOMES = [['fine', 'Still fine'], ['soggy', 'Went soggy / caked'], ['rancid', 'Smelled rancid'], ['mould', 'Mould'], ['fermented', 'Fermented / off-smell'], ['bruised', 'Bruised / soft'], ['other', 'Other']]

export default function Trace() {
  const { code } = useParams()
  const nav = useNavigate()
  const { t } = useT()
  const [d, setD] = useState(null)
  const [err, setErr] = useState(null)
  const [q, setQ] = useState('')
  const [batch, setBatch] = useState({ lot: '', packed_on: new Date().toISOString().slice(0, 10), quantity: 500 })
  const [fb, setFb] = useState({ observed_days: '', outcome: 'soggy', notes: '' })
  const [msg, setMsg] = useState(null)
  const load = () => api.trace(code).then(setD).catch((e) => setErr(e.message))
  useEffect(() => { if (code) { setD(null); setErr(null); load() } }, [code])

  if (!code) return (
    <div className="page" style={{ marginTop: 28, maxWidth: 640 }}>
      <form className="sheet stack" onSubmit={(e) => { e.preventDefault(); q && nav(`/t/${q.trim().toUpperCase()}`) }}>
        <div className="tape">{t('Trace a pack')}</div>
        <p className="muted">Scan the QR on a pack, or type the code printed under it.</p>
        <div className="row"><input value={q} onChange={(e) => setQ(e.target.value)} placeholder="AK-3F9C1A" aria-label="Trace code" style={{ flex: 1 }} /><button className="btn">Open</button></div>
      </form>
    </div>
  )
  if (err) return <div className="page" style={{ marginTop: 24 }}><div className="err">{err}</div></div>
  if (!d) return <div className="page" style={{ marginTop: 24 }}><Skeleton /></div>

  const addBatch = async (e) => { e.preventDefault(); await api.batch(code, { ...batch, quantity: +batch.quantity }); setMsg('Batch logged'); load() }
  const addFb = async (e) => {
    e.preventDefault()
    const r = await api.feedback(code, { ...fb, observed_days: +fb.observed_days })
    setMsg(`Thank you. The model for this food now uses ${r.calibration.n} field report${r.calibration.n > 1 ? 's' : ''} (correction ×${r.calibration.factor}).`)
    setFb({ ...fb, observed_days: '', notes: '' }); load()
  }
  return (
    <div className="page stack layers-in" style={{ '--g': '20px', marginTop: 20 }}>
      <section className="sheet lift verdict">
        <div className="stack" style={{ '--g': '10px' }}>
          <div className="row"><span className="pill ok">VERIFIED SPEC</span><span className="mono small">{d.code}</span></div>
          <h1 style={{ fontSize: 'clamp(26px,3vw,36px)' }}>{d.title}</h1>
          <p className="small muted">Specified by Anna Kavach on {new Date(d.created * 1000).toLocaleDateString('en-IN', { dateStyle: 'long' })}. <Link to={`/p/${d.project_id}`}>See the full analysis</Link>.</p>
        </div>
        <div className="qr"><img src={qrUrl(d.code)} alt={`QR for ${d.code}`} /></div>
      </section>
      <section className="sheet">
        <div className="tape">Pack specification</div>
        <table className="t"><tbody>{d.spec.map(([k, v], i) => <tr key={i}><td style={{ width: 180, fontWeight: 600 }}>{k}</td><td>{v}</td></tr>)}</tbody></table>
      </section>
      {msg && <div className="inset" role="status" style={{ fontWeight: 600 }}>{msg}</div>}
      <section className="grid2">
        <form className="sheet stack" onSubmit={addBatch}>
          <div className="tape">Batches packed to this spec</div>
          {d.batches.length ? <table className="t"><thead><tr><th>Lot</th><th>Packed on</th><th>Packs</th></tr></thead><tbody>
            {d.batches.map((b) => <tr key={b.id}><td className="mono">{b.lot}</td><td>{b.packed_on}</td><td className="num">{fmt(b.quantity)}</td></tr>)}</tbody></table>
            : <p className="muted small">No batches logged yet.</p>}
          <div className="fields">
            <label className="field"><span>Lot number</span><input required value={batch.lot} onChange={(e) => setBatch({ ...batch, lot: e.target.value })} placeholder="L-2026-041" /></label>
            <label className="field"><span>Packed on</span><input type="date" required value={batch.packed_on} onChange={(e) => setBatch({ ...batch, packed_on: e.target.value })} /></label>
            <label className="field"><span>Packs</span><input type="number" min="1" required value={batch.quantity} onChange={(e) => setBatch({ ...batch, quantity: e.target.value })} /></label>
          </div>
          <div><button className="btn ghost small">Log batch</button></div>
        </form>
        <form className="sheet stack" onSubmit={addFb}>
          <div className="tape">{t('Report real shelf life')}</div>
          <p className="small muted">How long did packs from this spec actually last? Every report corrects the model for this food.</p>
          <div className="fields">
            <label className="field"><span>Days until it went bad (or days so far)</span><input type="number" min="1" required value={fb.observed_days} onChange={(e) => setFb({ ...fb, observed_days: e.target.value })} /></label>
            <label className="field"><span>What happened</span><select value={fb.outcome} onChange={(e) => setFb({ ...fb, outcome: e.target.value })}>{OUTCOMES.map(([v, l]) => <option key={v} value={v}>{l}</option>)}</select></label>
            <label className="field" style={{ gridColumn: '1/-1' }}><span>Notes (optional)</span><input value={fb.notes} maxLength={500} onChange={(e) => setFb({ ...fb, notes: e.target.value })} placeholder="e.g. kept in a humid godown in July" /></label>
          </div>
          <div><button className="btn small">Send report</button></div>
          {d.feedback.length > 0 && <table className="t"><thead><tr><th>Predicted</th><th>Observed</th><th>Outcome</th></tr></thead><tbody>
            {d.feedback.map((f) => <tr key={f.id}><td className="num">{f.predicted_days ? `${fmt(f.predicted_days)} d` : '—'}</td><td className="num">{fmt(f.observed_days)} d</td><td>{f.outcome}</td></tr>)}</tbody></table>}
          <p className="tiny muted">Calibration for this food: ×{d.calibration.factor} from {d.calibration.n} report(s), shrunk toward 1 until more data arrives.</p>
        </form>
      </section>
    </div>
  )
}
