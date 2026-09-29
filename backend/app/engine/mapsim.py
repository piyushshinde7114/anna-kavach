"""Modified-atmosphere packaging for respiring produce.

Gas balance in the headspace (volume V, mL):
    V dyO2/dt  = (Pf(T) A + n Ph(T)) (0.21 - yO2) - W R(T, yO2)
    V dyCO2/dt = W RQ R(T, yO2) - (beta Pf(T) A + n beta_h Ph(T)) yCO2
Respiration: R = R13 Q10^((T-13)/10) yO2 / (Km + yO2)   (Michaelis-Menten in O2)
Film permeance: Arrhenius from 23 C; micro-perforation: Fickian diffusion through air (~T^1.75).
Design search is vectorised over every candidate; the chosen design is re-solved with an adaptive ODE solver.
"""
import numpy as np
from scipy.integrate import solve_ivp

EA_FILM = 35000.0
HOLE_O2 = 0.45  # mL O2 / (h.atm) per 100 um hole in a 25 um film at 25 C
BETA_HOLE = 0.78
MAP_FILMS = ["LDPE25", "LDPE50", "CPP30", "BOPP20"]
AREAS = [0.10, 0.14, 0.18, 0.22, 0.26, 0.30]
HOLES = np.arange(0, 305, 5)


def _temp_fn(legs):
    edges = np.cumsum([0] + [l["hours"] for l in legs])
    temps = np.array([l["temp_c"] for l in legs])
    def T(t):
        i = np.searchsorted(edges, t, side="right") - 1
        return temps[min(max(i, 0), len(temps) - 1)]
    return T, float(edges[-1])


def _film_perm(film, T):
    p23 = np.sqrt(film["otr"][0] * film["otr"][1]) / 24.0  # mL/(m2.h.atm)
    return p23 * np.exp(EA_FILM / 8.314 * (1 / 296.15 - 1 / (T + 273.15)))


def _basis_end(legs):
    t, seen_cold = 0.0, False
    for l in legs:
        if l["temp_c"] <= 15:
            seen_cold = True
        elif seen_cold:
            return t
        t += l["hours"]
    return t


def search(food, legs, films, kg):
    """Vectorised explicit integration over all (film, area, holes) designs."""
    T_of, H = _temp_fn(legs)
    basis = _basis_end(legs)
    designs = [(f, a, int(n)) for f in MAP_FILMS for a in AREAS for n in HOLES]
    P = np.array([[_film_perm(films[f], 23.0) / _film_perm(films[f], 23.0), a, n, films[f]["beta"]] for f, a, n in designs])
    film_idx = np.array([MAP_FILMS.index(f) for f, _, _ in designs])
    area, holes, beta = P[:, 1], P[:, 2], P[:, 3]
    V = 1000 * food["free_l_per_kg"] * kg
    o2 = np.full(len(designs), 0.21 * V)
    co2 = np.zeros(len(designs))
    dt = 0.02
    win = np.zeros(len(designs)); inj = np.zeros(len(designs))
    lo2, hi2 = food["o2_window"]; lc, hc = food["co2_window"]
    steps = int(H / dt)
    for k in range(steps):
        t = k * dt
        T = T_of(t)
        pf = np.array([_film_perm(films[f], T) for f in MAP_FILMS])[film_idx] * area
        ph = holes * HOLE_O2 * ((T + 273.15) / 298.15) ** 1.75
        y = np.maximum(o2 / V, 0); yc = co2 / V
        r = food["R13"] * food["Q10"] ** ((T - 13) / 10) * y / (food["Km"] + y) * kg
        o2 += ((pf + ph) * (0.21 - y) - r) * dt
        co2 += (food["RQ"] * r - (pf * beta + ph * BETA_HOLE) * yc) * dt
        if t < basis:
            O, C = 100 * y, 100 * yc
            win += ((O >= lo2) & (O <= hi2) & (C >= lc) & (C <= hc)) * dt
            inj += ((O < food["o2_min"]) | (C > food["co2_max"])) * dt
    score = np.where(inj > 0.05, -1e9, win - holes * 0.001 - area * 0.01)
    i = int(np.argmax(score))
    f, a, n = designs[i]
    return dict(film=f, area=a, holes=n, window_h=float(win[i]), feasible=bool(score[i] > -1e8), searched=len(designs), basis_end=basis, H=H)


def solve(food, legs, films, design, kg, vent_at=None, n_points=200):
    """Adaptive ODE solve (LSODA) for one design; returns curves and hours in window / injury."""
    T_of, H = _temp_fn(legs)
    V = 1000 * food["free_l_per_kg"] * kg
    film = films[design["film"]] if design.get("film") else None

    def rhs(t, s):
        T = T_of(t)
        y = max(s[0], 0); yc = max(s[1], 0)
        pf = _film_perm(film, T) * design["area"] if film else 0.0
        ph = design["holes"] * HOLE_O2 * ((T + 273.15) / 298.15) ** 1.75
        po2, pco2 = pf + ph, pf * (film["beta"] if film else 1) + ph * BETA_HOLE
        if vent_at is not None and t >= vent_at:
            po2 = pco2 = 4000.0
        r = food["R13"] * food["Q10"] ** ((T - 13) / 10) * y / (food["Km"] + y) * kg
        return [(po2 * (0.21 - y) - r) / V, (food["RQ"] * r - pco2 * yc) / V]

    edges = np.cumsum([0] + [l["hours"] for l in legs])
    ts = np.linspace(0, H, n_points)
    y0, pts = [0.21, 0.0], []
    t_all, o_all, c_all = [], [], []
    # integrate leg by leg (and split at the vent) so temperature steps are respected
    cuts = sorted(set(list(edges) + ([vent_at] if vent_at is not None else [])))
    for a, b in zip(cuts[:-1], cuts[1:]):
        if b - a <= 1e-9:
            continue
        te = ts[(ts >= a) & (ts <= b)]
        te = np.unique(np.concatenate([[a], te, [b]]))
        sol = solve_ivp(rhs, (a, b), y0, method="LSODA", t_eval=te, max_step=0.5, rtol=1e-6, atol=1e-9)
        t_all += list(sol.t); o_all += list(sol.y[0]); c_all += list(sol.y[1])
        y0 = [sol.y[0][-1], sol.y[1][-1]]
    t = np.array(t_all); O = 100 * np.array(o_all); C = 100 * np.array(c_all)
    order = np.argsort(t, kind="stable"); t, O, C = t[order], O[order], C[order]
    dt = np.diff(t, append=t[-1])
    lo2, hi2 = food["o2_window"]; lc, hc = food["co2_window"]
    inwin = (O >= lo2) & (O <= hi2) & (C >= lc) & (C <= hc)
    bad = (O < food["o2_min"]) | (C > food["co2_max"])
    first = float(t[bad][0]) if bad.any() else None
    step = max(1, len(t) // n_points)
    return dict(t=t[::step].round(2).tolist(), o2=O[::step].round(2).tolist(), co2=C[::step].round(2).tolist(),
                window_h=float((dt * inwin).sum()), injury_h=float((dt * bad).sum()), first_injury_h=first, H=H)


def evaluate(food, legs, films, kg):
    s = search(food, legs, films, kg)
    cold_h = sum(min(l["hours"], max(0, s["basis_end"] - sum(x["hours"] for x in legs[:i]))) for i, l in enumerate(legs) if l["temp_c"] <= 15) or s["basis_end"]
    baseline = dict(film="LDPE25", area=0.12, holes=0)
    base = solve(food, legs, films, baseline, kg)
    works = s["feasible"] and s["window_h"] >= 0.25 * cold_h
    out = dict(search=s, cold_h=cold_h, baseline=dict(design=baseline, sim=base), map_works=works)
    y_t = sum(food["o2_window"]) / 200
    r13 = food["R13"] * kg * y_t / (food["Km"] + y_t)
    out["requirement"] = dict(o2_window=food["o2_window"], co2_window=food["co2_window"], o2_min=food["o2_min"],
                              co2_max=food["co2_max"], chill_c=food["chill_c"], permeance_13=r13 / (0.21 - y_t))
    if works:
        d = dict(film=s["film"], area=s["area"], holes=s["holes"])
        sealed = solve(food, legs, films, d, kg)
        vent = None
        if sealed["injury_h"] > 0.05 and s["basis_end"] < s["H"]:
            vent = s["basis_end"]
            final = solve(food, legs, films, d, kg, vent_at=vent)
        else:
            final = sealed
        f = films[d["film"]]
        out.update(design=d, film_name=f["name"], sealed=sealed, final=final, vent_at=vent,
                   perm_film_13=float(_film_perm(f, 13) * d["area"]), perm_holes_13=float(d["holes"] * HOLE_O2 * (286.15 / 298.15) ** 1.75))
    out["chill_legs"] = [l["name"] for l in legs if l["temp_c"] < food["chill_c"]]
    return out
