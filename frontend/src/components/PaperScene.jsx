import { useRef } from 'react'

/* Hero illustration: a route drawn as layers of cut paper (sky, hills, road, truck, orchard, pouch).
   Each layer drifts a little with the pointer, deeper layers less, like a paper diorama. */
export default function PaperScene() {
  const ref = useRef(null)
  const move = (e) => {
    const el = ref.current; if (!el) return
    const r = el.getBoundingClientRect()
    const x = (e.clientX - r.left) / r.width - 0.5, y = (e.clientY - r.top) / r.height - 0.5
    el.querySelectorAll('[data-depth]').forEach((g) => {
      const d = +g.dataset.depth
      g.style.transform = `translate(${(-x * d * 14).toFixed(1)}px, ${(-y * d * 8).toFixed(1)}px)`
    })
  }
  const reset = () => ref.current?.querySelectorAll('[data-depth]').forEach((g) => (g.style.transform = ''))
  return (
    <svg ref={ref} className="scene" viewBox="0 0 600 440" role="img" aria-label="Paper-cut scene: an orchard, a refrigerated truck on the road and a sealed pouch"
      onPointerMove={move} onPointerLeave={reset}>
      <defs>
        <filter id="ps" x="-10%" y="-10%" width="120%" height="130%"><feDropShadow dx="0" dy="3" stdDeviation="3" floodColor="#0b1a14" floodOpacity=".28" /></filter>
        <filter id="ps2" x="-10%" y="-10%" width="120%" height="130%"><feDropShadow dx="0" dy="6" stdDeviation="5" floodColor="#0b1a14" floodOpacity=".32" /></filter>
        <clipPath id="frame"><rect width="600" height="440" rx="22" /></clipPath>
      </defs>
      <g clipPath="url(#frame)">
        <rect width="600" height="440" fill="var(--sc-sky)" />
        <g data-depth="0.2" style={{ transition: 'transform .3s ease-out' }}>
          <circle cx="470" cy="92" r="46" fill="var(--sc-sun)" filter="url(#ps)" />
          <path d="M60 80 q18 -16 36 0 q14 -12 28 0 q10 10 -4 14 h-58 q-14 -4 -2 -14z" fill="var(--sc-cloud)" filter="url(#ps)" />
        </g>
        <g data-depth="0.4" style={{ transition: 'transform .3s ease-out' }}>
          <path d="M-20 250 C 80 170, 170 200, 250 185 S 420 150, 520 190 S 620 200, 640 210 V 460 H -20z" fill="var(--sc-hill1)" filter="url(#ps)" />
        </g>
        <g data-depth="0.7" style={{ transition: 'transform .3s ease-out' }}>
          <path d="M-20 300 C 90 240, 200 280, 300 255 S 470 235, 640 270 V 460 H -20z" fill="var(--sc-hill2)" filter="url(#ps)" />
          <path d="M-20 360 C 120 330, 220 300, 330 312 S 520 330, 640 300 V 340 C 520 368, 420 346, 330 350 S 120 372, -20 396z" fill="var(--sc-road)" filter="url(#ps)" />
          <path d="M40 368 l40 -8 M150 350 l40 -6 M270 336 l40 -2 M400 340 l40 -2 M520 326 l40 -6" stroke="var(--sc-dash)" strokeWidth="4" strokeLinecap="round" />
          {/* reefer truck */}
          <g transform="translate(300 262) rotate(-2)" filter="url(#ps2)">
            <rect x="0" y="0" width="112" height="56" rx="6" fill="var(--sc-box)" />
            <rect x="8" y="10" width="40" height="18" rx="3" fill="var(--sc-hill2)" opacity=".9" />
            <text x="12" y="23" fontSize="11" fontWeight="700" fill="#fff" style={{ fontFamily: 'var(--f-num)' }}>13°C</text>
            <path d="M112 16 h28 l18 20 v20 h-46z" fill="var(--sc-cab)" />
            <path d="M118 22 h18 l12 14 h-30z" fill="var(--sc-sky)" />
            <circle cx="28" cy="60" r="11" fill="var(--sc-wheel)" /><circle cx="28" cy="60" r="4" fill="var(--sc-box)" />
            <circle cx="130" cy="60" r="11" fill="var(--sc-wheel)" /><circle cx="130" cy="60" r="4" fill="var(--sc-box)" />
          </g>
        </g>
        <g data-depth="1.1" style={{ transition: 'transform .3s ease-out' }}>
          <path d="M-20 400 C 100 360, 190 380, 260 392 S 420 440, 640 390 V 460 H -20z" fill="var(--sc-hill3)" filter="url(#ps2)" />
          {/* mango tree */}
          <rect x="92" y="300" width="14" height="74" rx="4" fill="var(--sc-trunk)" filter="url(#ps)" />
          <g filter="url(#ps2)">
            <circle cx="72" cy="290" r="34" fill="var(--sc-leaf)" /><circle cx="112" cy="272" r="40" fill="var(--sc-leaf2)" /><circle cx="140" cy="300" r="30" fill="var(--sc-leaf)" />
          </g>
          {[[80, 300], [118, 262], [140, 306], [100, 292], [62, 280]].map(([x, y], i) => (
            <ellipse key={i} cx={x} cy={y} rx="7" ry="9" fill="var(--sc-sun)" filter="url(#ps)" transform={`rotate(-20 ${x} ${y})`} />
          ))}
        </g>
        <g data-depth="1.6" style={{ transition: 'transform .3s ease-out' }}>
          {/* the pouch, as layered paper: outer, metal, sealant */}
          <g transform="translate(446 300) rotate(6)" filter="url(#ps2)">
            <path d="M0 10 q0 -10 10 -10 h92 q10 0 10 10 v118 h-112z" fill="#b9dcc8" />
            <path d="M4 14 q0 -8 8 -8 h84 q8 0 8 8 v110 h-100z" fill="#c3c8cf" />
            <path d="M8 18 q0 -6 6 -6 h80 q6 0 6 6 v106 h-92z" fill="var(--sc-pouch)" />
            <rect x="8" y="6" width="92" height="7" fill="var(--sc-seal)" opacity=".6" />
            <rect x="20" y="44" width="68" height="40" rx="6" fill="var(--sc-leaf2)" />
            <text x="54" y="69" textAnchor="middle" fontSize="15" fill="#fff" style={{ fontFamily: 'var(--f-deva)', fontWeight: 700 }}>अन्न कवच</text>
            <rect x="34" y="96" width="40" height="18" rx="3" fill="#fff" /><path d="M38 100h6v6h-6zM48 100h4v4h-4zM56 104h6v6h-6zM66 100h4v10h-4z" fill="#1d2433" />
          </g>
        </g>
      </g>
    </svg>
  )
}
