import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api.js'
import { useT } from '../i18n.jsx'
import { Skeleton } from '../components/bits.jsx'

export default function Projects() {
  const { t } = useT()
  const [rows, setRows] = useState(null)
  const [confirm, setConfirm] = useState(null)
  const load = () => api.projects().then(setRows).catch(() => setRows([]))
  useEffect(() => { load() }, [])
  const del = async (id) => { await api.del(id); setConfirm(null); load() }
  return (
    <div className="page stack" style={{ '--g': '18px', marginTop: 20 }}>
      <div className="row" style={{ justifyContent: 'space-between' }}><h1 style={{ fontSize: 36 }}>{t('My packs')}</h1><Link className="btn" to="/new">{t('New spec')}</Link></div>
      {!rows ? <Skeleton /> : rows.length === 0 ? (
        <div className="sheet"><p className="muted">No packs yet. <Link to="/new">Design the first one</Link>.</p></div>
      ) : (
        <div className="sheet"><div className="tscroll"><table className="t">
          <thead><tr><th>Product and route</th><th>Type</th><th>Trace code</th><th>Created</th><th></th></tr></thead>
          <tbody>{rows.map((p) => (
            <tr key={p.id}>
              <td><Link to={`/p/${p.id}`} style={{ fontWeight: 600 }}>{p.title}</Link></td>
              <td className="small">{p.kind}</td>
              <td className="mono small"><Link to={`/t/${p.trace_code}`}>{p.trace_code}</Link></td>
              <td className="small muted">{new Date(p.created * 1000).toLocaleString('en-IN', { dateStyle: 'medium', timeStyle: 'short' })}</td>
              <td style={{ textAlign: 'right' }}>{confirm === p.id
                ? <span className="row" style={{ '--g': '6px', justifyContent: 'flex-end' }}><button className="btn small" style={{ background: 'var(--chili)' }} onClick={() => del(p.id)}>Delete</button><button className="btn ghost small" onClick={() => setConfirm(null)}>Keep</button></span>
                : <button className="chipbtn" onClick={() => setConfirm(p.id)}>Delete…</button>}</td>
            </tr>))}</tbody>
        </table></div></div>
      )}
    </div>
  )
}
