async function req(path, opts = {}) {
  const r = await fetch(path, { headers: { 'Content-Type': 'application/json', ...(opts.headers || {}) }, ...opts })
  if (!r.ok) {
    let msg = `${r.status} ${r.statusText}`
    try { const j = await r.json(); msg = typeof j.detail === 'string' ? j.detail : (j.detail?.[0]?.msg || msg) } catch {}
    throw new Error(msg)
  }
  return r.json()
}
export const api = {
  meta: () => req('/api/meta'),
  foods: () => req('/api/foods'),
  films: () => req('/api/films'),
  estimate: (c) => req('/api/foods/estimate', { method: 'POST', body: JSON.stringify(c) }),
  intake: (text) => req('/api/intake', { method: 'POST', body: JSON.stringify({ text }) }),
  climate: (city) => req(`/api/climate/${encodeURIComponent(city)}`),
  recommend: (body) => req('/api/recommend', { method: 'POST', body: JSON.stringify(body) }),
  projects: () => req('/api/projects'),
  project: (id) => req(`/api/projects/${id}`),
  del: (id) => req(`/api/projects/${id}`, { method: 'DELETE' }),
  simulate: (id, legs) => req(`/api/projects/${id}/simulate`, { method: 'POST', body: JSON.stringify(legs) }),
  trace: (code) => req(`/api/trace/${code}`),
  batch: (code, b) => req(`/api/trace/${code}/batches`, { method: 'POST', body: JSON.stringify(b) }),
  feedback: (code, f) => req(`/api/trace/${code}/feedback`, { method: 'POST', body: JSON.stringify(f) }),
  adminCheck: (tok) => req('/api/admin/check', { method: 'POST', headers: { 'X-Admin-Token': tok } }),
  putFilm: (tok, id, body) => req(`/api/films/${id}`, { method: 'PUT', headers: { 'X-Admin-Token': tok }, body: JSON.stringify(body) }),
}
export const pdfUrl = (id) => `/api/projects/${id}/pdf`
export const qrUrl = (code) => `/api/qr/${code}.svg`
export const MONTHS = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
export const fmt = (x, d = 0) => (x == null || !Number.isFinite(+x)) ? '—' : (+x).toLocaleString('en-IN', { maximumFractionDigits: d, minimumFractionDigits: 0 })
export const rs = (a) => `₹${fmt(a[0], 1)}–${fmt(a[1], 1)}`
