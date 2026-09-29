import { useEffect, useMemo, useRef, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { api, fmt, pdfUrl, qrUrl, rs, MONTHS } from '../api.js'
import { useT } from '../i18n.jsx'
import { Conf, Laminate, Skeleton, useToast } from '../components/bits.jsx'
import { GasChart, Histogram, Pareto, SeasonChart, Tornado } from '../components/charts.jsx'

export default function Project() {
  const { id } = useParams()
  const [p, setP] = useState(null)
  const [err, setErr] = useState(null)
  useEffect(() => { setP(null); api.project(id).then(setP).catch((e) => setErr(e.message)) }, [id])
  if (err) return <div className="page" style={{ marginTop: 24 }}><div className="err">{err}</div></div>
  if (!p) return <div className="page" style={{ marginTop: 24 }}><Skeleton lines={8} /></div>
  const r = p.result
  return <div className="page stack layers-in" style={{ '--g': '22px', marginTop: 20 }}>{r.map ? <Produce r={r} /> : <Dry r={r} />}</div>
}

function Actions({ r }) {
  const { t } = useT()
  const [toast, say] = useToast()
  const link = `${location.origin}/t/${r.trace_code}`
  const copy = () => navigator.clipboard?.writeText(link).then(() => say('Trace link copied'), () => say(link))
  return (
    <div className="stack" style={{ '--g': '10px', alignItems: 'center' }}>
      <div className="qr"><img src={qrUrl(r.trace_code)} alt={`QR code for pack ${r.trace_code}`} /></div>
      <div className="mono small" style={{ fontWeight: 600 }}>{r.trace_code}</div>
      <a className="btn small" href={pdfUrl(r.project_id)} target="_blank" rel="noreferrer">{t('Download spec sheet (PDF)')}</a>
      <div className="row" style={{ '--g': '6px' }}>
        <Link className="btn ghost small" to={`/t/${r.trace_code}`}>{t('Open trace page')}</Link>
        <button type="button" className="btn ghost small" onClick={copy}>Copy link</button>
      </div>
      {toast}
    </div>
  )
}

function Modes({ modes }) {
  return <div className="row" style={{ '--g': '8px' }}>{modes.map((m) => <span key={m.mode} className="pill warn" title={m.why}>{m.mode}</span>)}</div>
}

/* ---------------------------------------------------------------- dry, fat, chilled, frozen */
function Dry({ r }) {
  const d = r.dry
  const byKey = useMemo(() => Object.fromEntries(d.candidates.map((c) => [c.ids.join('/'), c])), [d])
  const pickKey = (k) => d.picks[k]?.join('/')
  const green = byKey[pickKey('green')]
  const [sel, setSel] = useState(pickKey('green') || d.candidates[0].ids.join('/'))
  const [w, setW] = useState({ barrier: 3, cost: 3, carbon: 2, recycle: 3 })
  const [showAll, setShowAll] = useState(false)
  const moisture = d.kind === 'dry'
  const passing = d.candidates.filter((c) => c.pass)

  const balance = useMemo(() => {
    if (!passing.length) return null
    const norm = (vals, v, invert) => { const lo = Math.min(...vals), hi = Math.max(...vals); const x = hi === lo ? 0.5 : (v - lo) / (hi - lo); return invert ? 1 - x : x }
    const bar = passing.map((c) => moisture ? c.life.p10 : -c.otr[1]), cost = passing.map((c) => c.cost_pack[0] + c.cost_pack[1]),
      co2 = passing.map((c) => c.co2e_pack_g), rec = passing.map((c) => c.eco.rank)
    const scored = passing.map((c, i) => ({ c, s: w.barrier * norm(bar, bar[i]) + w.cost * norm(cost, cost[i], true) + w.carbon * norm(co2, co2[i], true) + w.recycle * norm(rec, rec[i], true) }))
    return scored.sort((a, b) => b.s - a.s)[0].c
  }, [w, d])

  const s = byKey[sel]
  const target = r.target_days
  const lifeText = (c) => c.life ? (c.life.capped ? `> ${fmt(c.life.horizon)} d` : `${fmt(c.life.p10)}–${fmt(c.life.p90)} d`) : '—'
  const req = d.requirement
  const cal = r.calibration
  const monthIdx = MONTHS.findIndex((m) => m.startsWith(r.month.slice(0, 3)))
  const points = d.candidates.map((c) => ({ key: c.ids.join('/'), name: c.name, cost: (c.cost_pack[0] + c.cost_pack[1]) / 2, co2: c.co2e_pack_g, pass: c.pass, pareto: c.pareto }))
  const headline = green
    ? moisture ? `${green.name} keeps ${r.food.name.toLowerCase()} within spec for ${lifeText(green)}` : `${green.name} meets every barrier rule for ${r.food.name.toLowerCase()}`
    : `No composed pack reaches ${target} days. Shorten the target, shrink the pouch or store in air-conditioning.`

  return (
    <>
      <section className="sheet lift verdict">
        <div className="stack" style={{ '--g': '12px' }}>
          <div className="row"><span className={`pill ${green ? 'ok' : 'bad'}`}>{green ? 'SPEC READY' : 'NOTHING PASSES'}</span>
            <span className="small muted">{r.food.name} · {r.pack.weight_g} g · target {target} days · {r.climate.city ? `sold in ${r.climate.city}` : 'Indian ambient'} · dispatch {r.month}</span></div>
          <h1 style={{ fontSize: 'clamp(26px,3.2vw,38px)' }}>{headline}</h1>
          <p className="muted">
            {moisture ? `Moisture sets the clock: the pack may let in only ${fmt(req.wvtr_max, 2)} g of water per m² per day (tropical test). ` : ''}
            {req.otr_max ? `${req.o2_note}. ` : ''}{req.opaque ? 'Light-sensitive, so an opaque layer is required. ' : ''}
            {d.kind === 'chilled' ? 'Microbial growth, not the film, limits paneer; the pack must hold vacuum and the cold chain must hold 4 °C. ' : ''}
            {d.kind === 'frozen' ? 'At −18 °C the film must stay flexible and stop ice subliming (freezer burn). ' : ''}
          </p>
          <Modes modes={r.failure_modes} />
          <p className="tiny muted">Climate: {r.climate.source}. {cal?.n ? `Calibrated with ${cal.n} field report${cal.n > 1 ? 's' : ''} (×${cal.factor}).` : 'No field reports yet for this food.'}</p>
        </div>
        <Actions r={r} />
      </section>

      <section className="sheet">
        <div className="tape">What the food needs</div>
        <div className="needs">
          {moisture && <div className="need"><div className="v">≤ {fmt(req.wvtr_max, 2)}</div><div className="k">WVTR, g/m²·day at 38 °C / 90 % RH</div></div>}
          {moisture && <div className="need"><div className="v">{fmt(req.water_allowed_g, 1)} g</div><div className="k">water the pack may let in over {target} days</div></div>}
          <div className="need"><div className="v">{req.otr_max ? `≤ ${req.otr_max}` : 'Any'}</div><div className="k">OTR, cc/m²·day·atm{req.n2_flush ? ' + nitrogen flush' : ''}</div></div>
          <div className="need"><div className="v">{req.opaque ? 'Opaque' : 'Clear OK'}</div><div className="k">light protection</div></div>
          {req.store_c != null && <div className="need"><div className="v">{req.store_c} °C</div><div className="k">storage temperature the film must survive</div></div>}
          {req.degas && <div className="need"><div className="v">Valve</div><div className="k">one-way degassing valve for CO₂ from roasting</div></div>}
        </div>
      </section>

      <section className="stack" style={{ '--g': '14px' }}>
        <div className="tape">Three packs that pass</div>
        <div className="picks">
          {[['barrier', 'Best barrier'], ['value', 'Best value'], ['green', 'Greenest that passes']].map(([k, label]) => {
            const c = byKey[pickKey(k)]
            if (!c) return <div key={k} className="pick"><div className="kind">{label}</div><p className="muted">Nothing passes.</p></div>
            return (
              <button type="button" key={k} className={`pick ${k === 'green' ? 'hero' : ''}`} style={{ textAlign: 'left', border: 0, cursor: 'pointer', font: 'inherit', color: 'inherit' }} onClick={() => setSel(c.ids.join('/'))}>
                {k === 'green' && <span className="stamp">RECOMMENDED</span>}
                <div className="kind">{label}</div>
                <Laminate layers={c.layers} />
                <div className="name">{c.name}</div>
                <dl className="kv">
                  <dt>WVTR</dt><dd className="num">{fmt(c.wvtr[0], 2)}–{fmt(c.wvtr[1], 2)}</dd>
                  <dt>OTR</dt><dd className="num">{fmt(c.otr[0], 2)}–{fmt(c.otr[1], 1)}</dd>
                  {moisture && <><dt>Shelf life</dt><dd><b className="num">{lifeText(c)}</b> <span className="tiny muted">P10–P90</span></dd></>}
                  <dt>Film cost</dt><dd className="num">{rs(c.cost_pack)} / pack</dd>
                  <dt>Carbon</dt><dd className="num">{fmt(c.co2e_pack_g, 1)} g CO₂e</dd>
                  <dt>End of life</dt><dd>{c.eco.label} · {c.eco.epr}</dd>
                </dl>
                {c.notes.map((n) => <p key={n} className="small" style={{ color: 'var(--chili)' }}>{n}</p>)}
              </button>
            )
          })}
        </div>
      </section>

      {passing.length > 1 && (
        <section className="grid2">
          <div className="sheet">
            <div className="tape">Your own balance</div>
            <p className="small muted" style={{ marginBottom: 12 }}>Move the sliders to say what matters to you. The pick updates from the {passing.length} packs that pass.</p>
            <div className="stack" style={{ '--g': '10px' }}>
              {[['barrier', 'Longer shelf life'], ['cost', 'Lower cost'], ['carbon', 'Lower carbon'], ['recycle', 'Easier to recycle']].map(([k, l]) => (
                <label key={k} className="row" style={{ '--g': '12px' }}><span style={{ width: 150 }} className="small">{l}</span>
                  <input type="range" min="0" max="5" value={w[k]} onChange={(e) => setW({ ...w, [k]: +e.target.value })} style={{ flex: 1 }} aria-label={l} />
                  <span className="num small" style={{ width: 14 }}>{w[k]}</span></label>
              ))}
            </div>
            {balance && <button type="button" className="inset" style={{ marginTop: 14, width: '100%', textAlign: 'left', border: 0, cursor: 'pointer', font: 'inherit', color: 'inherit' }} onClick={() => setSel(balance.ids.join('/'))}>
              <div className="label">Your pick</div><div className="mono" style={{ fontWeight: 600, marginTop: 4 }}>{balance.name}</div>
              <div className="small muted">{rs(balance.cost_pack)} · {fmt(balance.co2e_pack_g, 1)} g CO₂e · {balance.eco.label}{moisture ? ` · ${lifeText(balance)}` : ''}</div>
            </button>}
          </div>
          <div className="sheet">
            <div className="tape">Cost against carbon</div>
            <Pareto points={points} selected={sel} onSelect={setSel} />
            <div className="legend"><span><i style={{ background: 'var(--leaf)' }} />best trade-offs (Pareto)</span><span><i style={{ background: 'var(--leaf-2)', opacity: .5 }} />passes</span><span><i style={{ border: '1.5px solid var(--ink-2)', height: 8, width: 8, borderRadius: 9 }} />fails</span></div>
          </div>
        </section>
      )}

      {s && moisture && s.life && (
        <section className="grid2">
          <div className="sheet">
            <div className="tape">1,000 simulated packs · {s.name}</div>
            <Histogram hist={s.hist} horizon={s.life.horizon} target={target} life={s.life} />
            <p className="small" style={{ marginTop: 8 }}>
              9 in 10 packs last at least <b className="num">{fmt(s.life.p10)} days</b>; half last <b className="num">{s.life.capped ? `over ${fmt(s.life.horizon)}` : fmt(s.life.p50)}</b>.
              The spread comes from the film's supplier range, the uncertain crisp limit, and the weather year to year.
            </p>
          </div>
          {d.analysis?.season && (
            <div className="sheet">
              <div className="tape">When you ship matters</div>
              <SeasonChart season={d.analysis.season} target={target} current={monthIdx} />
              <p className="small" style={{ marginTop: 8 }}>Median shelf life of the recommended pack by dispatch month, using {r.climate.city || 'ambient'} weather. Monsoon months eat the moisture allowance fastest.</p>
            </div>
          )}
        </section>
      )}

      {d.analysis?.tornado && (
        <section className="grid2">
          <div className="sheet">
            <div className="tape">What moves the answer most</div>
            <Tornado items={d.analysis.tornado} base={d.analysis.base_life} />
            <p className="small muted" style={{ marginTop: 6 }}>Top bar = the input worth measuring first. Red: worse case, green: better case.</p>
          </div>
          <div className="sheet">
            <div className="tape">What if…</div>
            <table className="t"><tbody>
              {d.analysis.whatif.map((x) => (
                <tr key={x.label}><td>{x.label}</td><td className="num" style={{ textAlign: 'right' }}><b className={`mk ${x.life >= target ? 'ok' : 'bad'}`}>{x.life >= d.horizon - 1 ? `> ${fmt(d.horizon)}` : fmt(x.life)} d</b></td></tr>
              ))}
            </tbody></table>
          </div>
        </section>
      )}

      <section className="sheet">
        <div className="row" style={{ justifyContent: 'space-between' }}>
          <div className="tape">Every laminate the composer built · {d.candidates.length}</div>
          <button type="button" className="chipbtn" aria-pressed={showAll} onClick={() => setShowAll(!showAll)}>{showAll ? 'Show passing only' : 'Show failures too'}</button>
        </div>
        <div className="tscroll"><table className="t">
          <thead><tr><th>Structure</th>{moisture && <th>Shelf life P10–P90</th>}<th>OTR</th><th>Cost / pack</th><th>CO₂e</th><th>End of life</th><th>Result</th></tr></thead>
          <tbody>{d.candidates.filter((c) => showAll || c.pass).map((c) => (
            <tr key={c.ids.join('/')} className={c.pass ? '' : 'fail'} onClick={() => setSel(c.ids.join('/'))} style={{ cursor: 'pointer', background: sel === c.ids.join('/') ? 'var(--leaf-soft)' : undefined }}>
              <td className="mono small">{c.name}{c.pareto && <span className="pill ok" style={{ marginLeft: 6, padding: '1px 7px' }}>Pareto</span>}</td>
              {moisture && <td className="num">{lifeText(c)}</td>}
              <td className="num">{fmt(c.otr[1], c.otr[1] < 10 ? 2 : 0)}</td>
              <td className="num">{rs(c.cost_pack)}</td><td className="num">{fmt(c.co2e_pack_g, 1)} g</td><td>{c.eco.label}</td>
              <td>{c.pass ? <span className="mk ok">Pass</span> : <span className="small"><span className="mk bad">Fail</span> · {c.why.join('; ')}</span>}</td>
            </tr>))}</tbody>
        </table></div>
      </section>

      {moisture && d.calc && (
        <section className="grid2">
          <div className="sheet">
            <div className="tape">The maths, with your numbers</div>
            <pre className="eq">{`Dry solids      Ws = ${r.pack.weight_g} ÷ (1 + ${r.food.mi / 100}) = ${fmt(d.calc.Ws, 1)} g
Water allowed   Ws × (mc − mi) = ${fmt(d.calc.Ws, 1)} × (${r.food.mc / 100} − ${r.food.mi / 100}) = ${fmt(d.calc.water_allowed_g, 2)} g
Pouch area      A = 2 × ${r.pack.width_cm} × ${r.pack.height_cm} cm = ${fmt(d.calc.area_m2, 3)} m²
Weather load    Σ Δp(T,RH)/Δp(38 °C, 90 %) over ${target} d = ${fmt(d.calc.mean_factor * target, 1)} test-days
WVTR needed     ≤ ${fmt(d.calc.water_allowed_g, 2)} ÷ (${fmt(d.calc.area_m2, 3)} × ${fmt(d.calc.mean_factor * target, 1)}) = ${fmt(req.wvtr_max, 2)} g/m²·d
Laminate        1 / WVTR = Σ 1 / WVTRᵢ     (layers in series)
Shelf life      day when Σ WVTR·A·Δp/Δp_test reaches the allowance,
                sampled 1,000 times over film, limit and weather ranges`}</pre>
          </div>
          <div className="sheet">
            <div className="tape">Inputs and how sure we are</div>
            <table className="t"><tbody>
              <tr><td>Initial moisture</td><td className="num">{r.food.mi} % db</td><td><Conf c={r.food.conf.mi || 'typical'} /></td></tr>
              <tr><td>Crisp / caking limit</td><td className="num">{r.food.mc} % db</td><td><Conf c={r.food.conf.mc || 'assumed'} /></td></tr>
              <tr><td>Water activity inside</td><td className="num">{r.food.aw_in}</td><td><Conf c={r.food.conf.aw_in || 'assumed'} /></td></tr>
              <tr><td>Fat</td><td className="num">{r.food.fat} %</td><td><Conf c={r.food.conf.fat || 'typical'} /></td></tr>
              <tr><td>Film barrier values</td><td>supplier ranges</td><td><Conf c="typical" /></td></tr>
              <tr><td>Film cost</td><td>converter bands</td><td><Conf c="demo" /></td></tr>
              <tr><td>Weather</td><td className="small">{r.climate.source}</td><td><Conf c={r.climate.source.startsWith('Open-Meteo') ? 'sourced' : 'typical'} /></td></tr>
            </tbody></table>
            {r.estimate && <p className="small" style={{ marginTop: 10 }}>Properties estimated from {r.estimate.neighbours.map((n) => n.name).join(', ')} (confidence {r.estimate.level}).</p>}
          </div>
        </section>
      )}
      <Sources r={r} />
    </>
  )
}

/* ---------------------------------------------------------------- fresh produce (MAP) */
function Produce({ r }) {
  const m = r.map
  const food = r.food
  const [legs, setLegs] = useState(r.legs)
  const [sim, setSim] = useState(m.final || null)
  const [base, setBase] = useState(m.baseline.sim)
  const [busy, setBusy] = useState(false)
  const first = useRef(true)
  useEffect(() => {
    if (first.current) { first.current = false; return }
    const h = setTimeout(() => { setBusy(true); api.simulate(r.project_id, legs).then((x) => { setSim(m.map_works ? x.sim : null); setBase(x.baseline) }).finally(() => setBusy(false)) }, 300)
    return () => clearTimeout(h)
  }, [legs])
  const changed = legs.some((l, i) => l.temp_c !== r.legs[i].temp_c)
  const d = m.design
  const pill = m.map_works ? (m.vent_at != null ? ['warn', 'SPEC READY · 1 HANDLING RULE'] : ['ok', 'SPEC READY']) : ['bad', 'SEALED MAP NOT RECOMMENDED']
  const name = food.name.split(' (')[0].split(',')[0].toLowerCase()
  const headline = m.map_works
    ? `${m.film_name} bag, ${fmt(d.area, 2)} m², ${d.holes} micro-perforations keeps ${name} in its target gas for ${fmt(m.sealed.window_h)} h`
    : `Sealed film cannot hold ${name} in its target gas on this route. Use a macro-perforated bag or ventilated crate and protect the cold chain.`
  return (
    <>
      <section className="sheet lift verdict">
        <div className="stack" style={{ '--g': '12px' }}>
          <div className="row"><span className={`pill ${pill[0]}`}>{pill[1]}</span>
            <span className="small muted">{food.name} · {r.fill_kg} kg per bag{r.route?.distance_km ? ` · ${r.route.origin} → ${r.route.destination}, ${fmt(r.route.distance_km)} km, ${fmt(r.route.transit_h, 1)} h on the road` : ''} · {r.month}</span></div>
          <h1 style={{ fontSize: 'clamp(26px,3.2vw,38px)' }}>{headline}</h1>
          {m.map_works && m.vent_at != null && <p><b>Handling rule:</b> open the bag or pull the vent strip when it leaves the cold chain (hour {fmt(m.vent_at)}). Left sealed, O₂ drops below {food.o2_min} % at hour {fmt(m.sealed.first_injury_h, 1)} and the fruit spends {fmt(m.sealed.injury_h)} h in the injury zone.</p>}
          {!m.map_works && <p className="muted">The best sealed design found stays in the target window only {fmt(m.search.window_h)} h of {fmt(m.cold_h)} cold hours. Film and holes cannot reach {food.co2_window[0]}–{food.co2_window[1]} % CO₂ at {food.o2_window[0]}–{food.o2_window[1]} % O₂.</p>}
          <Modes modes={r.failure_modes} />
          {m.chill_legs.length > 0 && <p className="err" style={{ padding: '8px 12px' }}>Chilling risk: {m.chill_legs.join(', ')} run below {food.chill_c} °C.</p>}
        </div>
        <Actions r={r} />
      </section>

      <section className="sheet">
        <div className="tape">What the food needs</div>
        <div className="needs">
          <div className="need"><div className="v">{food.o2_window[0]}–{food.o2_window[1]} %</div><div className="k">O₂ in the bag (never below {food.o2_min} %) <Conf c={food.conf.window} /></div></div>
          <div className="need"><div className="v">{food.co2_window[0]}–{food.co2_window[1]} %</div><div className="k">CO₂ in the bag (never above {food.co2_max} %)</div></div>
          <div className="need"><div className="v">≈ {fmt(m.requirement.permeance_13)}</div><div className="k">O₂ transfer the bag must allow, mL/h·atm at 13 °C</div></div>
          <div className="need"><div className="v">≥ {food.chill_c} °C</div><div className="k">chilling limit</div></div>
        </div>
      </section>

      <section className="sheet">
        <div className="tape">Gas inside the bag, hour by hour</div>
        <div className="chartwrap"><GasChart legs={legs} sim={sim} baseline={base} food={food} /></div>
        <div className="legend" style={{ marginTop: 8 }}>
          {sim && <><span><i style={{ background: 'var(--leaf)' }} />O₂, recommended{m.vent_at != null ? ' + vent rule' : ''}</span><span><i style={{ background: 'var(--mango)' }} />CO₂, recommended</span></>}
          <span><i style={{ background: 'var(--chili)' }} />O₂ in a plain sealed LDPE bag</span><span><i style={{ background: 'var(--leaf)', opacity: .25, height: 10 }} />target O₂</span>
        </div>
        <div className="inset" style={{ marginTop: 14 }}>
          <div className="row" style={{ justifyContent: 'space-between' }}><b>Stress test: change any leg's temperature</b>{busy && <span className="tiny muted">re-solving…</span>}
            {changed && <button type="button" className="chipbtn" onClick={() => setLegs(r.legs)}>Reset</button>}</div>
          <div className="stack" style={{ '--g': '8px', marginTop: 10 }}>
            {legs.map((l, i) => (
              <label key={i} className="row" style={{ '--g': '12px' }}><span className="small" style={{ width: 230 }}>{l.name} · {fmt(l.hours, 1)} h</span>
                <input type="range" min="0" max="40" value={l.temp_c} onChange={(e) => setLegs(legs.map((x, j) => j === i ? { ...x, temp_c: +e.target.value } : x))} style={{ flex: 1 }} aria-label={`${l.name} temperature`} />
                <span className="num" style={{ width: 70, textAlign: 'right', whiteSpace: 'nowrap' }}>{l.temp_c} °C</span></label>
            ))}
          </div>
          {sim && changed && <p className="small" style={{ marginTop: 10 }}>{sim.injury_h > 0.05
            ? <><b className="mk bad">This pack fails:</b> {fmt(sim.injury_h)} h in the injury zone, first at hour {fmt(sim.first_injury_h, 1)}. Recompute the spec for this route.</>
            : <><b className="mk ok">Still holds:</b> {fmt(sim.window_h)} h in the target window, no injury.</>}</p>}
        </div>
      </section>

      <section className="grid2">
        <div className="sheet">
          <div className="tape">Designs compared</div>
          <table className="t"><thead><tr><th>Design</th><th>In window</th><th>Injury</th></tr></thead><tbody>
            <tr><td className="small">Plain sealed LDPE 25 µm, 0.12 m², no holes</td><td className="num">{fmt(m.baseline.sim.window_h)} h</td><td className="num mk bad">{fmt(m.baseline.sim.injury_h)} h</td></tr>
            {m.map_works && <tr><td className="small">{m.film_name}, {fmt(d.area, 2)} m², {d.holes} holes, left sealed</td><td className="num">{fmt(m.sealed.window_h)} h</td><td className={`num mk ${m.sealed.injury_h > 0.05 ? 'bad' : 'ok'}`}>{fmt(m.sealed.injury_h)} h</td></tr>}
            {m.map_works && m.vent_at != null && <tr><td className="small"><b>Same + vent on arrival</b></td><td className="num">{fmt(m.final.window_h)} h</td><td className="num mk ok">{fmt(m.final.injury_h)} h</td></tr>}
            {!m.map_works && <tr><td className="small"><b>Macro-perforated bag / ventilated crate + cold chain</b></td><td>no MAP</td><td className="num mk ok">0 h</td></tr>}
          </tbody></table>
          <p className="small muted" style={{ marginTop: 10 }}>The optimiser tried {fmt(m.search.searched)} designs (4 films × 6 bag sizes × 0–300 holes), integrating the gas balance for each over the whole trip; the winner is re-solved with an adaptive ODE solver.</p>
        </div>
        <div className="sheet">
          <div className="tape">The maths, with your numbers</div>
          <pre className="eq">{`Respiration  R(T) = ${food.R13} × ${food.Q10}^((T − 13)/10) × yO₂/(${food.Km} + yO₂)
             mL O₂ per kg per hour
Gas balance  V·dyO₂/dt = (P_film·A + n·P_hole)(0.21 − yO₂) − W·R
             V·dyCO₂/dt = W·RQ·R − (β·P_film·A + βₕ·n·P_hole)·yCO₂
Film         P(T) = P₂₃·exp(−Ea/R·(1/T − 1/296)),  Ea 35 kJ/mol
Hole         ≈ 0.45 mL/h·atm per 100 µm hole, Fick in air
Need @13 °C  ≈ ${fmt(m.requirement.permeance_13)} mL/h·atm${m.map_works ? `
Chosen       film ${fmt(m.perm_film_13)} + holes ${fmt(m.perm_holes_13)} mL/h·atm` : ''}`}</pre>
          <p className="small" style={{ marginTop: 8 }}>Respiration rate <Conf c={food.conf.respiration} /> — published values vary up to 3×. Run a one-day closed-jar test before scale-up.</p>
        </div>
      </section>
      <Sources r={r} />
    </>
  )
}

function Sources({ r }) {
  return (
    <section className="sheet flat">
      <div className="tape">Sources</div>
      <ul className="small" style={{ margin: 0, paddingLeft: 18, columns: 2, columnGap: 28 }}>
        {r.sources.map((s) => <li key={s.key}><a href={s.url} target="_blank" rel="noreferrer">{s.title}</a></li>)}
      </ul>
    </section>
  )
}
