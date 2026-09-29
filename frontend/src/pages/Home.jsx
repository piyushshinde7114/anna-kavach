import { useEffect, useRef, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { api } from '../api.js'
import { useT } from '../i18n.jsx'
import PaperScene from '../components/PaperScene.jsx'

const EXAMPLES = [
  '200 g banana chips 6 months Kochi to Delhi in May',
  '1 kg Alphonso mango Ratnagiri to Delhi, reefer truck',
  '500 g roasted peanuts 6 months Pune to Patna',
  '1 किलो आम रत्नागिरी से दिल्ली',
]

export function useVoice(onText, lang) {
  const [on, setOn] = useState(false)
  const rec = useRef(null)
  const SR = typeof window !== 'undefined' && (window.SpeechRecognition || window.webkitSpeechRecognition)
  const toggle = () => {
    if (!SR) return
    if (on) { rec.current?.stop(); return }
    const r = new SR(); rec.current = r
    r.lang = lang === 'hi' ? 'hi-IN' : 'en-IN'; r.interimResults = false
    r.onresult = (e) => onText(e.results[0][0].transcript)
    r.onend = () => setOn(false); r.onerror = () => setOn(false)
    setOn(true); r.start()
  }
  return { supported: !!SR, on, toggle }
}

export default function Home() {
  const { t, lang } = useT()
  const nav = useNavigate()
  const [text, setText] = useState('')
  const [busy, setBusy] = useState(false)
  const [err, setErr] = useState(null)
  const [meta, setMeta] = useState(null)
  const [recent, setRecent] = useState([])
  useEffect(() => { api.meta().then(setMeta).catch(() => {}); api.projects().then((p) => setRecent(p.slice(0, 4))).catch(() => {}) }, [])
  const voice = useVoice((s) => setText(s), lang)

  const go = async (q) => {
    const s = (q ?? text).trim(); if (!s) return
    setBusy(true); setErr(null)
    try {
      const r = await api.intake(s)
      if (!r.parsed.food_id) { setErr('I could not tell which food this is. Pick it from the list on the next screen.'); nav('/new', { state: { parsed: r.parsed, heard: s } }); return }
      nav('/new', { state: { parsed: r.parsed, heard: s } })
    } catch (e) { setErr(e.message) } finally { setBusy(false) }
  }

  return (
    <div className="page">
      <section className="hero">
        <div className="stack" style={{ '--g': '22px' }}>
          <div className="label">For food makers, FPOs and packaging buyers</div>
          <h1 className="display">{t('hero.title')}</h1>
          <p className="lede">{t('hero.lede')}</p>
          <form className="ask" onSubmit={(e) => { e.preventDefault(); go() }}>
            <label htmlFor="ask" className="sr" style={{ position: 'absolute', left: -9999 }}>Describe your product and route</label>
            <input id="ask" value={text} onChange={(e) => setText(e.target.value)} placeholder={t('ask.placeholder')} autoComplete="off" />
            {voice.supported && <button type="button" className="mic" aria-pressed={voice.on} onClick={voice.toggle} title={t('Speak')} aria-label={t('Speak')}>🎙</button>}
            <button className="btn" disabled={busy}>{busy ? '…' : t('Compute')}</button>
          </form>
          {err && <div className="err">{err}</div>}
          <div className="try" aria-label={t('Try')}>
            {EXAMPLES.map((e) => <button key={e} type="button" onClick={() => { setText(e); go(e) }}>{e}</button>)}
          </div>
          <div className="row small muted">or <Link to="/new">fill in the guided form</Link></div>
        </div>
        <PaperScene />
      </section>

      <section className="steps" style={{ marginTop: 26 }}>
        <div className="step"><b>1 · Know the food</b><span className="small muted">Moisture, fat, water activity and breathing rate decide how it spoils.</span></div>
        <div className="step"><b>2 · Map the journey</b><span className="small muted">Real monthly weather for your route, leg by leg, truck and shop.</span></div>
        <div className="step"><b>3 · Compute the barrier</b><span className="small muted">How much water, oxygen and gas exchange the pack may allow.</span></div>
        <div className="step"><b>4 · Choose the pack</b><span className="small muted">Laminates that pass, ranked on cost, carbon and recyclability, with the maths.</span></div>
      </section>

      <section className="grid2" style={{ marginTop: 28 }}>
        <div className="sheet stacked">
          <div className="tape">In the library</div>
          <div className="row" style={{ '--g': '28px' }}>
            <div><div className="num" style={{ fontSize: 34, fontWeight: 600 }}>{meta?.counts.foods ?? '—'}</div><div className="small muted">food commodities</div></div>
            <div><div className="num" style={{ fontSize: 34, fontWeight: 600 }}>{meta?.counts.films ?? '—'}</div><div className="small muted">film grades</div></div>
            <div><div className="num" style={{ fontSize: 34, fontWeight: 600 }}>{meta?.cities.length ?? '—'}</div><div className="small muted">Indian cities with live climate</div></div>
            <div><div className="num" style={{ fontSize: 34, fontWeight: 600 }}>{meta?.counts.reports ?? '—'}</div><div className="small muted">field reports learned from</div></div>
          </div>
        </div>
        <div className="sheet">
          <div className="tape">Recent packs</div>
          {recent.length === 0 ? <p className="muted">Your computed packs will appear here. Try one of the examples above.</p> :
            <div className="stack" style={{ '--g': '8px' }}>
              {recent.map((p) => (
                <Link key={p.id} to={`/p/${p.id}`} className="row" style={{ justifyContent: 'space-between', textDecoration: 'none', color: 'var(--ink)' }}>
                  <span style={{ fontWeight: 600 }}>{p.title}</span><span className="mono tiny muted">{p.trace_code}</span>
                </Link>
              ))}
            </div>}
        </div>
      </section>
    </div>
  )
}
