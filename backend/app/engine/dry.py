"""Shelf-stable, chilled and frozen foods: barrier budget, composer checks, Monte Carlo shelf life, Pareto ranking."""
import numpy as np
from .physics import psat_kpa, DP_TEST, arrhenius, O2_MG_PER_ML
from .laminate import all_structures, build

N_MC = 1000
PACK_ALLOWANCE = 1.15  # seals + trim waste on film area
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def _cum_factor(climate, start_month, days, aw_in, rng=None, n=1, jitter=False):
    """Cumulative sum over days of dp(T,RH)/dp_test, shape (n, days). Month changes every 30.44 days."""
    months = (start_month + (np.arange(days) / 30.44).astype(int)) % 12
    T = np.array([climate[m]["T"] for m in months])[None, :].repeat(n, 0)
    RH = np.array([climate[m]["RH"] for m in months])[None, :].repeat(n, 0)
    aw = np.full((n, 1), aw_in)
    if jitter:
        T = T + rng.normal(0, 1.5, (n, 1))
        RH = np.clip(RH + rng.normal(0, 0.05, (n, 1)), 0.05, 0.99)
        aw = np.clip(aw + rng.normal(0, 0.04, (n, 1)), 0.05, 0.95)
    ps = 0.61078 * np.exp(17.27 * T / (T + 237.3))
    f = np.clip(ps * (RH - aw), 0, None) / DP_TEST
    return np.cumsum(f, axis=1)


def _life_from_cum(cum, thresh):
    """Days until cumulative ingress reaches thresh (per sample). cum: (n, D), thresh: (n,)."""
    return (cum < thresh[:, None]).sum(axis=1).astype(float)


def evaluate(food, pack, target_days, climate, start_month, films, lam_cost, o2_rules, calib=1.0, seed=7):
    rng = np.random.default_rng(seed)
    W = float(pack["weight_g"])
    A = 2 * pack["width_cm"] * pack["height_cm"] / 1e4
    kind = food["kind"]
    store_T = food.get("store_c")
    t_mean = float(np.mean([c["T"] for c in climate])) if store_T is None else store_T
    rule = o2_rules.get(food.get("o2") or "low", o2_rules["low"])
    horizon = int(min(1460, max(6 * target_days, 365)))

    moisture = kind == "dry"
    req = None
    if moisture:
        mi, mc, aw_in = food["mi"] / 100, food["mc"] / 100, food["aw_in"]
        Ws = W / (1 + mi)
        allowed = Ws * (mc - mi)
        cum_det = _cum_factor(climate, start_month, max(target_days, 1), aw_in)[0]
        wvtr_req = allowed / (A * cum_det[-1]) if cum_det[-1] > 0 else float("inf")
        # Monte Carlo inputs shared by all structures
        cum_mc = _cum_factor(climate, start_month, horizon, aw_in, rng, N_MC, jitter=True)
        mc_s = mc * (1 + rng.normal(0, 0.12 if food["conf"].get("mc") == "assumed" else 0.05, N_MC))
        mc_s = np.maximum(mc_s, mi + 0.002)
        allowed_s = Ws * (mc_s - mi)
        u = rng.random(N_MC)
        cum_det_h = _cum_factor(climate, start_month, horizon, aw_in)[0]
        req = dict(wvtr_max=wvtr_req, water_allowed_g=allowed, Ws=Ws, area_m2=A,
                   mean_factor=float(cum_det[-1] / max(target_days, 1)))

    rows = []
    for ids in all_structures():
        s = build(ids, films, lam_cost)
        why, notes = [], []
        # --- moisture
        if moisture:
            lo, hi = s["wvtr"]
            w_s = np.exp(np.log(lo) + u * (np.log(hi) - np.log(lo)))
            life = _life_from_cum(cum_mc, allowed_s / (w_s * A)) * calib
            p10, p50, p90 = np.percentile(life, [10, 50, 90])
            s["life"] = dict(p10=float(p10), p50=float(p50), p90=float(p90), capped=bool(p50 >= horizon * calib - 1), horizon=horizon)
            s["hist"] = np.histogram(np.minimum(life, horizon), bins=24, range=(0, horizon))[0].tolist()
            s["_w_mid"] = float(np.sqrt(lo * hi))
            if p10 < target_days:
                why.append(f"moisture: 90 % of packs last only {p10:.0f} d")
        # --- oxygen / aroma / microbial rule
        if rule["otr_max"] is not None and s["otr"][1] > rule["otr_max"]:
            why.append(f"O₂ barrier: OTR up to {s['otr'][1]:.0f} > {rule['otr_max']} cc/m²·d")
        if food.get("light") and target_days > 60 and not s["opaque"]:
            why.append("light-sensitive: needs an opaque layer")
        if not s["seal"]:
            why.append("no heat-seal layer")
        if (food.get("fat") or 0) >= 15 and s["grease"] == "poor":
            why.append("sealant not grease-resistant")
        if store_T is not None and store_T < s["tmin"]:
            why.append(f"brittle below {s['tmin']} °C")
        if kind == "frozen" and s["tmin"] > -25:
            why.append("not rated for −25 °C")
        if kind == "frozen" and s["wvtr"][1] > 10:
            why.append("freezer burn risk: WVTR > 10")
        if kind == "chilled" and not s["vacuum_ok"]:
            why.append("needs a vacuum-capable barrier (nylon, EVOH or metallised)")
        if food.get("degas"):
            notes.append("add a one-way degassing valve (roasted coffee releases CO₂)")
        # --- oxygen ingress (always reported, mg O2 per kg food over the target)
        otr_mid = float(np.sqrt(s["otr"][0] * s["otr"][1]))
        s["o2_ingress_mg_kg"] = arrhenius(otr_mid, 30000, t_mean, 23) * 0.21 * A * target_days * O2_MG_PER_ML / (W / 1000)
        s["cost_pack"] = [c * A * PACK_ALLOWANCE for c in s["cost_m2"]]
        s["co2e_pack_g"] = s["co2e_m2"] * A * PACK_ALLOWANCE * 1000
        s["pass"] = not why
        s["why"], s["notes"] = why, notes
        rows.append(s)

    passing = [r for r in rows if r["pass"]]
    key_barrier = (lambda r: r["life"]["p10"]) if moisture else (lambda r: -r["otr"][1])
    picks = {}
    if passing:
        picks["barrier"] = max(passing, key=key_barrier)
        picks["value"] = min(passing, key=lambda r: (sum(r["cost_pack"]), -key_barrier(r)))
        picks["green"] = min(passing, key=lambda r: (r["eco"]["rank"], r["co2e_pack_g"], sum(r["cost_pack"])))
    # Pareto front over passing: min cost, min CO2e, min eco rank, max barrier
    def dominates(a, b):
        ka = (sum(a["cost_pack"]), a["co2e_pack_g"], a["eco"]["rank"], -key_barrier(a))
        kb = (sum(b["cost_pack"]), b["co2e_pack_g"], b["eco"]["rank"], -key_barrier(b))
        return all(x <= y for x, y in zip(ka, kb)) and any(x < y for x, y in zip(ka, kb))
    for r in passing:
        r["pareto"] = not any(dominates(o, r) for o in passing if o is not r)

    rec = picks.get("green")
    analysis = {}
    if moisture and rec is not None:
        analysis = _analysis(food, pack, target_days, climate, start_month, rec, req, calib, horizon)

    for r in rows:
        r.pop("_w_mid", None)
    rows.sort(key=lambda r: (not r["pass"], -(r["life"]["p10"] if moisture else -r["otr"][1])))
    return dict(kind=kind, area_m2=A, requirement=dict(
        wvtr_max=req["wvtr_max"] if req else None, water_allowed_g=req["water_allowed_g"] if req else None,
        otr_max=rule["otr_max"], n2_flush=rule["n2_flush"], o2_note=rule["note"], light=bool(food.get("light")),
        opaque=bool(food.get("light")) and target_days > 60, store_c=store_T, t_mean=t_mean,
        degas=bool(food.get("degas"))), calc=req, candidates=rows,
        picks={k: v["ids"] for k, v in picks.items()}, analysis=analysis, horizon=horizon, calibration=calib)


def _life_det(food, pack, days_h, climate, start_month, wvtr, calib, mc_scale=1.0, aw_d=0.0, T_d=0.0, RH_d=0.0, A_scale=1.0):
    cl = [dict(T=c["T"] + T_d, RH=min(0.99, max(0.05, c["RH"] + RH_d))) for c in climate]
    mi, mc = food["mi"] / 100, food["mc"] / 100 * mc_scale
    W = pack["weight_g"]
    A = 2 * pack["width_cm"] * pack["height_cm"] / 1e4 * A_scale
    allowed = W / (1 + mi) * max(mc - mi, 1e-4)
    cum = _cum_factor(cl, start_month, days_h, food["aw_in"] + aw_d)[0]
    return float((cum < allowed / (wvtr * A)).sum()) * calib


def _analysis(food, pack, target, climate, start_month, rec, req, calib, horizon):
    lo, hi = rec["wvtr"]
    mid = float(np.sqrt(lo * hi))
    base = _life_det(food, pack, horizon, climate, start_month, mid, calib)
    tests = [
        ("Film WVTR (supplier range)", dict(wvtr=hi), dict(wvtr=lo)),
        ("Crisp / caking moisture limit ±15 %", dict(mc_scale=0.85), dict(mc_scale=1.15)),
        ("Storage humidity ±5 % RH", dict(RH_d=0.05), dict(RH_d=-0.05)),
        ("Storage temperature ±2 °C", dict(T_d=2), dict(T_d=-2)),
        ("Pouch size ±15 %", dict(A_scale=1.15), dict(A_scale=0.85)),
        ("Food water activity ±0.05", dict(aw_d=0.05), dict(aw_d=-0.05)),
    ]
    tornado = []
    for label, worse, better in tests:
        args = dict(wvtr=mid)
        w = _life_det(food, pack, horizon, climate, start_month, **{**args, **worse}, calib=calib)
        b = _life_det(food, pack, horizon, climate, start_month, **{**args, **better}, calib=calib)
        tornado.append(dict(label=label, low=w, high=b, span=abs(b - w)))
    tornado.sort(key=lambda t: -t["span"])
    season = [dict(month=MONTHS[m], life=_life_det(food, pack, horizon, climate, m, mid, calib)) for m in range(12)]
    ac = [dict(T=25.0, RH=0.60)] * 12
    whatif = [
        dict(label="As planned", life=base),
        dict(label=f"Dispatch in {max(season, key=lambda s: s['life'])['month']} (best month)", life=max(s["life"] for s in season)),
        dict(label=f"Dispatch in {min(season, key=lambda s: s['life'])['month']} (worst month)", life=min(s["life"] for s in season)),
        dict(label="Stored in an air-conditioned shop (25 °C / 60 %)", life=_life_det(food, pack, horizon, ac, 0, mid, calib)),
        dict(label="Pouch 20 % smaller, same fill", life=_life_det(food, pack, horizon, climate, start_month, mid, calib, A_scale=0.8)),
    ]
    return dict(base_life=base, tornado=tornado, season=season, whatif=whatif, horizon=horizon, wvtr_used=mid)
