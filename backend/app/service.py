"""Orchestrates a recommendation: profile -> journey/climate -> engine -> explanation -> saved project."""
import time
from . import db, climate
from .data.seed import CITIES, LAMINATION_COST_M2, O2_RULES, SOURCES
from .engine import dry, mapsim
from .engine.journey import build_legs
from .engine.profiler import Estimator, failure_modes

MONTHS = dry.MONTHS


class InputError(ValueError):
    pass


def resolve_food(inp, foods):
    if inp.get("food_id"):
        f = next((x for x in foods if x["id"] == inp["food_id"]), None)
        if not f:
            raise InputError("Unknown food. Pick one from the list or describe its composition.")
        return dict(f), None
    c = inp.get("custom")
    if not c:
        raise InputError("Choose a food or describe a new one.")
    est = Estimator(foods).estimate(c)
    f = dict(id="custom", name=c.get("name") or "Custom food", hi=c.get("name") or "", kind="dry", category="Custom",
             mi=c["mi"], mc=est["mc"], aw_in=est["aw_in"], fat=c["fat"], protein=c["protein"], carb=c["carb"], ph=6.0,
             o2=est["o2"], light=est["light"], conf=dict(mi="user", mc="estimated", fat="user", aw_in="estimated"), source="ifct")
    return f, est


def recommend(inp):
    foods, films = db.foods(), db.films()
    food, estimate = resolve_food(inp, foods)
    route = inp.get("route") or {}
    month = int(route.get("month", time.localtime().tm_mon - 1))
    route["month"] = month
    for k in ("origin", "destination"):
        if route.get(k) and route[k] not in CITIES:
            raise InputError(f"Unknown city: {route[k]}")
    out = dict(food=food, estimate=estimate, failure_modes=failure_modes(food), month=MONTHS[month],
               sources=[dict(key=k, **SOURCES[k]) for k in {food.get("source", "robertson"), "robertson", "fssai_pack", "pwm_2022", "openmeteo"} if k in SOURCES])
    if food["kind"] == "produce":
        kg = float(inp.get("fill_kg") or food.get("fill_kg", 1.0))
        if inp.get("legs"):
            legs = [dict(name=l["name"], hours=float(l["hours"]), temp_c=float(l["temp_c"])) for l in inp["legs"]]
            out["route"] = dict(custom=True)
        else:
            if not (route.get("origin") and route.get("destination")):
                raise InputError("Fresh produce needs a route: pick where it is packed and where it is sold.")
            co, so = climate.monthly(route["origin"])
            cd, sd = climate.monthly(route["destination"])
            j = build_legs(route, CITIES, co, cd, food)
            legs = j["legs"]
            out["route"] = dict(**route, distance_km=j["distance_km"], transit_h=j["transit_h"], climate_source=sd,
                                origin_climate=co[month], dest_climate=cd[month])
        out["legs"] = legs
        out["fill_kg"] = kg
        out["map"] = mapsim.evaluate(food, legs, films, kg)
    else:
        pack = inp.get("pack") or food.get("pack")
        target = int(inp.get("target_days") or food.get("target_days", 180))
        city = route.get("destination") or route.get("origin")
        if food["kind"] in ("chilled", "frozen"):
            clim, src = [dict(T=food["store_c"], RH=0.9)] * 12, f"cold chain at {food['store_c']} °C"
        elif city:
            clim, src = climate.monthly(city)
        else:
            clim, src = climate.FALLBACK, "Indian ambient default (28 °C / 72 % RH)"
        if inp.get("storage") == "ac":
            clim, src = [dict(T=25.0, RH=0.60)] * 12, "air-conditioned store (25 °C / 60 % RH)"
        cal = db.calibration(food["id"]) if food["id"] != "custom" else dict(factor=1.0, n=0)
        res = dry.evaluate(food, pack, target, clim, month, films, LAMINATION_COST_M2, O2_RULES, calib=cal["factor"])
        out.update(pack=pack, target_days=target, climate=dict(city=city, source=src, months=clim), calibration=cal, dry=res)
    title = f"{food['name']}" + (f" · {route.get('origin')} → {route.get('destination')}" if route.get("origin") and route.get("destination") else "")
    pid, code = db.save_project(title, food["id"], food["kind"], inp, out)
    out["project_id"], out["trace_code"] = pid, code
    return out


def resimulate(pid, legs):
    p = db.get_project(pid)
    if not p or "map" not in p["result"]:
        raise InputError("This project has no produce simulation.")
    r = p["result"]
    m = r["map"]
    films = db.films()
    food = r["food"]
    d = m.get("design") or m["baseline"]["design"]
    legs = [dict(name=l["name"], hours=float(l["hours"]), temp_c=float(l["temp_c"])) for l in legs]
    sim = mapsim.solve(food, legs, films, d, r["fill_kg"], vent_at=m.get("vent_at"))
    base = mapsim.solve(food, legs, films, m["baseline"]["design"], r["fill_kg"])
    return dict(sim=sim, baseline=base)
