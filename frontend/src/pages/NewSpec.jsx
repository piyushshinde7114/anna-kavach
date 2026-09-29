import { useEffect, useMemo, useState } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import { api, MONTHS, fmt } from '../api.js'
import { useT } from '../i18n.jsx'
import { Skeleton } from '../components/bits.jsx'

const KIND_LABEL = { dry: 'Dry & processed', fat: 'Oils & fats', chilled: 'Chilled', frozen: 'Frozen', produce: 'Fresh produce' }

export default function NewSpec() {
  const { t, lang } = useT()
  const nav = useNavigate()
  const loc = useLocation()
  const pre = loc.state?.parsed || {}
  const [meta, setMeta] = useState(null)
  const [cat, setCat] = useState('all')
  const [q, setQ] = useState('')
  const [foodId, setFoodId] = useState(pre.food_id || null)
  const [custom, setCustom] = useState(null)
  const [est, setEst] = useState(null)
  const [pack, setPack] = useState({ weight_g: 200, width_cm: 15, height_cm: 22 })
  const [target, setTarget] = useState(180)
  const [fill, setFill] = useState(1)
  const [route, setRoute] = useState({ origin: pre.origin || '', destination: pre.destination || '', month: pre.month ?? new Date().getMonth(), mode: pre.mode || 'reefer', retail_hours: 48, transit_c: '' })
  const [busy, setBusy] = useState(false)
  const [err, setErr] = useState(null)

  useEffect(() => { api.meta().then(setMeta).catch((e) => setErr(e.message)) }, [])
  const food = meta?.foods.find((f) => f.id === foodId)
  // defaults when a food is chosen
  useEffect(() => {
    if (!food) return
    if (food.pack) setPack({ ...food.pack, ...(pre.weight_g && food.kind !== 'produce' ? { weight_g: pre.weight_g } : {}) })
    setTarget(pre.target_days || food.target_days || 180)
    if (food.kind === 'produce') setFill(pre.weight_g ? pre.weight_g / 1000 : food.fill_kg || 1)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [foodId, meta])
  // live composition estimate for a custom food
  useEffect(() => {
    if (!custom) { setEst(null); return }
    const h = setTimeout(() => api.estimate(custom).then(setEst).catch(() => setEst(null)), 350)
    return () => clearTimeout(h)
  }, [custom])

  const cats = useMemo(() => meta ? ['all', ...new Set(meta.foods.map((f) => f.kind))] : [], [meta])
  const shown = meta?.foods.filter((f) => (cat === 'all' || f.kind === cat) && (!q || (f.name + ' ' + (f.hi || '')).toLowerCase().includes(q.toLowerCase()))) || []
  const isProduce = food?.kind === 'produce'
  const needsRoute = isProduce
  const setR = (k, v) => setRoute((r) => ({ ...r, [k]: v }))

  const submit = async (e) => {
    e.preventDefault(); setErr(null)
    if (!foodId && !custom) { setErr('Choose a food, or describe a new one.'); return }
    if (needsRoute && (!route.origin || !route.destination)) { setErr('Fresh produce needs a route: choose where it is packed and where it is sold.'); return }
    const body = { target_days: +target }
    if (custom) Object.assign(body, { custom: { ...custom, mi: +custom.mi, fat: +custom.fat, protein: +custom.protein, carb: +custom.carb }, pack: { weight_g: +pack.weight_g, width_cm: +pack.width_cm, height_cm: +pack.height_cm } })
    else body.food_id = foodId
    if (!isProduce && !custom) body.pack = { weight_g: +pack.weight_g, width_cm: +pack.width_cm, height_cm: +pack.height_cm }
    if (isProduce) body.fill_kg = +fill
    const r = { month: +route.month, mode: route.mode, retail_hours: +route.retail_hours }
    if (route.origin) r.origin = route.origin
    if (route.destination) r.destination = route.destination
    if (route.transit_c !== '') r.transit_c = +route.transit_c
    body.route = r
    setBusy(true)
    try { const res = await api.recommend(body); nav(`/p/${res.project_id}`) } catch (e2) { setErr(e2.message); setBusy(false) }
  }

  if (!meta) return <div className="page" style={{ marginTop: 24 }}>{err ? <div className="err">Could not reach the Anna Kavach server: {err}</div> : <Skeleton lines={6} />}</div>
  const cityOpt = meta.cities.map((c) => <option key={c.name} value={c.name}>{lang === 'hi' && c.hi ? `${c.hi} · ${c.name}` : c.name}</option>)

  return (
    <form className="page stack layers-in" style={{ '--g': '22px', marginTop: 20 }} onSubmit={submit}>
      <div>
        <h1 style={{ fontSize: 36 }}>{t('New spec')}</h1>
        {loc.state?.heard && <p className="muted" style={{ marginTop: 6 }}>Heard: “{loc.state.heard}”. I filled in what I understood; check it and add the rest.</p>}
      </div>

      <section className="sheet">
        <div className="tape">1 · {t('What do you pack?')}</div>
        <div className="row" style={{ justifyContent: 'space-between', marginBottom: 12 }}>
          <div className="tabs">
            {cats.map((c) => <button type="button" key={c} className="chipbtn" aria-pressed={cat === c} onClick={() => setCat(c)}>{c === 'all' ? 'All' : KIND_LABEL[c]}</button>)}
          </div>
          <input style={{ maxWidth: 260 }} placeholder="Search foods" value={q} onChange={(e) => setQ(e.target.value)} aria-label="Search foods" />
        </div>
        <div className="foodgrid" role="listbox" aria-label="Foods">
          {shown.map((f) => (
            <button type="button" key={f.id} className="foodbtn" aria-pressed={foodId === f.id} onClick={() => { setFoodId(f.id); setCustom(null) }}>
              {f.name}<small>{f.hi}</small>
            </button>
          ))}
          <button type="button" className="foodbtn" aria-pressed={!!custom} onClick={() => { setFoodId(null); setCustom({ name: '', mi: 3, fat: 25, protein: 5, carb: 60 }) }}>
            + {t('Not in the list? Describe it')}<small>dry or snack foods</small>
          </button>
        </div>
        {custom && (
          <div className="grid2" style={{ marginTop: 16 }}>
            <div className="fields">
              <label className="field" style={{ gridColumn: '1/-1' }}><span>Product name</span><input value={custom.name} onChange={(e) => setCustom({ ...custom, name: e.target.value })} placeholder="e.g. Jackfruit chips" /></label>
              {[['mi', 'Moisture % (dry basis)'], ['fat', 'Fat %'], ['protein', 'Protein %'], ['carb', 'Carbohydrate %']].map(([k, l]) => (
                <label className="field" key={k}><span>{l}</span><input type="number" step="0.1" min="0" max="100" value={custom[k]} onChange={(e) => setCustom({ ...custom, [k]: e.target.value })} /></label>
              ))}
            </div>
            <div className="inset small">
              <div className="label" style={{ marginBottom: 6 }}>Estimated from similar foods</div>
              {!est ? <div className="skeleton" /> : <>
                <p>Crisp / caking limit ≈ <b className="num">{est.mc}%</b>, water activity ≈ <b className="num">{est.aw_in}</b>, oxygen risk <b>{est.o2}</b>{est.light ? ', light-sensitive' : ''}.</p>
                <p style={{ marginTop: 6 }}>Confidence <b>{est.level}</b> ({fmt(est.confidence * 100)}%). Closest: {est.neighbours.map((n) => `${n.name} (${fmt(n.similarity * 100)}%)`).join(', ')}.</p>
                {est.level !== 'good' && <p style={{ marginTop: 6, color: 'var(--chili)' }}>Measure a sorption isotherm before trusting the shelf life.</p>}
              </>}
            </div>
          </div>
        )}
      </section>

      <section className="grid2">
        <div className="sheet">
          <div className="tape">2 · {t('Pack and shelf life')}</div>
          {isProduce ? (
            <div className="fields">
              <label className="field"><span>{t('Fill per bag (kg)')}</span><input type="number" step="0.25" min="0.25" max="25" value={fill} onChange={(e) => setFill(e.target.value)} /></label>
              <p className="small muted" style={{ gridColumn: '1/-1' }}>For fresh produce the engine sizes the bag and its perforations itself; you only set the fill.</p>
            </div>
          ) : (
            <div className="fields">
              <label className="field"><span>{t('Pack weight (g)')}</span><input type="number" min="10" value={pack.weight_g} onChange={(e) => setPack({ ...pack, weight_g: e.target.value })} /></label>
              <label className="field"><span>{t('Pouch width (cm)')}</span><input type="number" step="0.5" min="4" value={pack.width_cm} onChange={(e) => setPack({ ...pack, width_cm: e.target.value })} /></label>
              <label className="field"><span>{t('Pouch height (cm)')}</span><input type="number" step="0.5" min="4" value={pack.height_cm} onChange={(e) => setPack({ ...pack, height_cm: e.target.value })} /></label>
              <label className="field"><span>{t('Target shelf life (days)')}</span><input type="number" min="3" max="1000" value={target} onChange={(e) => setTarget(e.target.value)} /></label>
            </div>
          )}
        </div>
        <div className="sheet">
          <div className="tape">3 · {t('Journey')}</div>
          <div className="fields">
            <label className="field"><span>{t('Packed at')}</span><select value={route.origin} onChange={(e) => setR('origin', e.target.value)}><option value="">{isProduce ? 'Choose a city' : 'Optional'}</option>{cityOpt}</select></label>
            <label className="field"><span>{t('Sold in')}</span><select value={route.destination} onChange={(e) => setR('destination', e.target.value)}><option value="">{isProduce ? 'Choose a city' : 'Optional'}</option>{cityOpt}</select></label>
            <label className="field"><span>{t('Dispatch month')}</span><select value={route.month} onChange={(e) => setR('month', e.target.value)}>{MONTHS.map((m, i) => <option key={m} value={i}>{m}</option>)}</select></label>
            {isProduce && <>
              <label className="field"><span>{t('Transport')}</span><select value={route.mode} onChange={(e) => setR('mode', e.target.value)}>
                <option value="reefer">{t('Reefer truck')}</option><option value="truck">{t('Ambient truck')}</option><option value="rail">{t('Rail')}</option></select></label>
              {route.mode === 'reefer' && <label className="field"><span>Reefer setpoint (°C)</span><input type="number" placeholder={food?.store_c ?? 13} value={route.transit_c} onChange={(e) => setR('transit_c', e.target.value)} /></label>}
              <label className="field"><span>{t('Hours at retail')}</span><input type="number" min="0" max="400" value={route.retail_hours} onChange={(e) => setR('retail_hours', e.target.value)} /></label>
            </>}
          </div>
          {!isProduce && <p className="small muted" style={{ marginTop: 10 }}>The shelf life is computed with real month-by-month weather at the selling city, starting from the dispatch month.</p>}
        </div>
      </section>

      {err && <div className="err">{err}</div>}
      <div className="row"><button className="btn mango" disabled={busy} style={{ fontSize: 17, padding: '14px 22px' }}>{busy ? `${t('Working it out')}…` : t('Design my pack')}</button>
        {busy && <span className="small muted">Fetching route climate, composing laminates, running 1,000 simulated packs each…</span>}</div>
    </form>
  )
}
