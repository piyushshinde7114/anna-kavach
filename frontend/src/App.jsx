import { useEffect, useState } from 'react'
import { NavLink, Route, Routes, Link } from 'react-router-dom'
import { useT } from './i18n.jsx'
import Home from './pages/Home.jsx'
import NewSpec from './pages/NewSpec.jsx'
import Project from './pages/Project.jsx'
import Projects from './pages/Projects.jsx'
import Trace from './pages/Trace.jsx'
import Library from './pages/Library.jsx'
import Admin from './pages/Admin.jsx'

function Toggles() {
  const { lang, setLang } = useT()
  const [theme, setTheme] = useState(() => { try { return localStorage.getItem('ak-theme') || 'system' } catch { return 'system' } })
  useEffect(() => {
    const r = document.documentElement
    theme === 'system' ? r.removeAttribute('data-theme') : r.setAttribute('data-theme', theme)
    try { localStorage.setItem('ak-theme', theme) } catch {}
  }, [theme])
  const next = { system: 'light', light: 'dark', dark: 'system' }
  return (
    <div className="toggles">
      <button className="chipbtn" aria-pressed={lang === 'hi'} onClick={() => setLang(lang === 'hi' ? 'en' : 'hi')} title="Language">{lang === 'hi' ? 'हिं' : 'EN'}</button>
      <button className="chipbtn" onClick={() => setTheme(next[theme])} title="Theme">{theme === 'system' ? 'Auto' : theme === 'light' ? 'Day' : 'Night'}</button>
    </div>
  )
}

export default function App() {
  const { t } = useT()
  return (
    <>
      <header className="topbar">
        <div className="in">
          <Link to="/" className="brand"><span className="mark">Anna Kavach</span><span className="deva">अन्न कवच</span></Link>
          <nav className="nav" aria-label="Main">
            <NavLink to="/new">{t('New spec')}</NavLink>
            <NavLink to="/projects">{t('My packs')}</NavLink>
            <NavLink to="/library">{t('Library')}</NavLink>
            <NavLink to="/t">{t('Trace a pack')}</NavLink>
            <NavLink to="/admin">{t('Admin')}</NavLink>
          </nav>
          <Toggles />
        </div>
      </header>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/new" element={<NewSpec />} />
        <Route path="/p/:id" element={<Project />} />
        <Route path="/projects" element={<Projects />} />
        <Route path="/t" element={<Trace />} />
        <Route path="/t/:code" element={<Trace />} />
        <Route path="/library" element={<Library />} />
        <Route path="/admin" element={<Admin />} />
        <Route path="*" element={<div className="page"><div className="sheet" style={{ marginTop: 24 }}><h2>Page not found</h2><p className="muted">Go back to <Link to="/">the start</Link>.</p></div></div>} />
      </Routes>
      <footer className="foot">
        Anna Kavach advises; it does not certify food safety. Film values are indicative ranges until replaced by supplier datasheets. Climate: Open-Meteo archive. Gas targets: UC Davis Postharvest Center. SIH26236 · MoFPI.
      </footer>
    </>
  )
}
